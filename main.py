from wakeword.porcupine_adapter import WakewordDetector
from utils.logger import logger

def on_wake():
    logger.info("唤醒成功！（此处可加入后续录音/ASR/TTS流程）")

if __name__ == "__main__":
    detector = WakewordDetector()
    detector.start(on_wake)
