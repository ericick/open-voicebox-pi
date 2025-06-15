import pvporcupine
import sounddevice as sd
import numpy as np
from utils.config_loader import load_config
from utils.logger import logger

class WakewordDetector:
    def __init__(self, config_path="config/config.yaml"):
        self.config = load_config(config_path)
        self.access_key = self.config["wakeword"]["access_key"]
        self.keyword_paths = self.config["wakeword"]["keyword_paths"]

        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=self.keyword_paths
        )
        self.audio_stream = None
        self.frame_length = self.porcupine.frame_length
        self.sampling_rate = self.porcupine.sample_rate

    def start(self, callback):
        logger.info("Wakeword detector started. Waiting for: {}".format(self.keyword_paths))
        with sd.InputStream(channels=1, samplerate=self.sampling_rate, dtype='int16', blocksize=self.frame_length) as stream:
            while True:
                pcm = stream.read(self.frame_length)[0].flatten()
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    logger.info("Wakeword detected!")
                    callback()  # 调用外部回调，进入录音等后续流程

    def __del__(self):
        if self.porcupine is not None:
            self.porcupine.delete()
