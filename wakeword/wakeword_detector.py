import os

import numpy as np
import sherpa_onnx
import sounddevice as sd

from utils.logger import logger


class WakewordDetector:
    """基于 sherpa-onnx 的离线中文唤醒词检测（替换原 Porcupine 实现）。"""

    def __init__(
        self,
        model_dir,
        keywords_file,
        audio_device_index=None,
        channels=4,
        keywords_score=1.0,
        keywords_threshold=0.25,
        num_threads=2,
        sample_rate=16000,
        feature_dim=80,
    ):
        self.model_dir = model_dir
        self.keywords_file = keywords_file
        self.audio_device_index = audio_device_index
        self.channels = channels
        self.sample_rate = sample_rate

        encoder = os.path.join(model_dir, "encoder-epoch-13-avg-2-chunk-16-left-64.onnx")
        decoder = os.path.join(model_dir, "decoder-epoch-13-avg-2-chunk-16-left-64.onnx")
        joiner = os.path.join(model_dir, "joiner-epoch-13-avg-2-chunk-16-left-64.onnx")
        tokens = os.path.join(model_dir, "tokens.txt")

        self.kws = sherpa_onnx.KeywordSpotter(
            tokens=tokens,
            encoder=encoder,
            decoder=decoder,
            joiner=joiner,
            keywords_file=keywords_file,
            num_threads=num_threads,
            keywords_score=keywords_score,
            keywords_threshold=keywords_threshold,
            provider="cpu",
        )

    def start(self, callback):
        """持续监听麦克风，检测到唤醒词后释放资源并回调。"""
        stream = self.kws.create_stream()
        logger.info("唤醒词检测已启动，等待唤醒...")
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                blocksize=1600,
                device=self.audio_device_index,
            ) as mic:
                while True:
                    pcm, _ = mic.read(1600)
                    mono = np.ascontiguousarray(pcm[:, 0])
                    samples = mono.astype(np.float32) / 32768.0
                    stream.accept_waveform(self.sample_rate, samples)
                    if self.kws.is_ready(stream):
                        self.kws.decode_stream(stream)
                        keyword = self.kws.get_result(stream)
                        if keyword:
                            logger.info(f"检测到唤醒词: {keyword}")
                            self.kws.reset_stream(stream)
                            break
        except KeyboardInterrupt:
            logger.info("唤醒词检测终止。")
        # 资源释放后再回调
        callback()
