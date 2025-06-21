import pvporcupine
import pyaudio
from utils.logger import logger

class WakewordDetector:
    def __init__(self, keyword_paths, access_key, sensitivities=None, audio_device_index=None):
        self.keyword_paths = keyword_paths
        self.access_key = access_key
        self.sensitivities = sensitivities
        self.model_path = model_path
        self.audio_device_index = audio_device_index

    def start(self, callback):
        porcupine = pvporcupine.create(
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            sensitivities=self.sensitivities
            model_path=self.model_path
        )
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=self.audio_device_index
        )
        logger.info("唤醒词检测已启动，等待唤醒...")
        try:
            while True:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = memoryview(pcm).cast('h')
                result = porcupine.process(pcm)
                if result >= 0:
                    logger.debug("唤醒词已检测到，触发回调。")
                    callback()
        except KeyboardInterrupt:
            logger.info("唤醒词检测终止。")
        finally:
            stream.close()
            pa.terminate()
            porcupine.delete()
