from wakeword.porcupine_adapter import WakewordDetector
from audio_in.recorder import Recorder
from asr.xunfei_asr import XunfeiASR
from dialogue.deepseek_adapter import DeepseekAdapter
from tts.xunfei_adapter import XunfeiTTS
from audio_out.player import play_audio
from endword.endword_detector import EndwordDetector
from utils.config_loader import load_config
from utils.logger import logger

def main():
    # 加载配置
    config = load_config()
    # 初始化各核心模块
    recorder = Recorder()
    asr = XunfeiASR(
        app_id=config["xunfei_asr"]["app_id"],
        api_key=config["xunfei_asr"]["api_key"],
        api_secret=config["xunfei_asr"]["api_secret"]
    )
    deepseek = DeepseekAdapter(api_key=config["deepseek"]["api_key"])
    tts = XunfeiTTS(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"]
    )
    endword_detector = EndwordDetector(keywords=config["endwords"])

    def on_wake():
        logger.info("唤醒成功，准备录音。")
        audio = recorder.record()
        if audio is None or len(audio) == 0:
            logger.warning("未录到有效语音。")
            return
        user_text = asr.recognize(audio)
        logger.info(f"语音识别结果：{user_text}")

        if not user_text.strip():
            reply_text = "我没有听清，你可以再说一遍吗？"
        elif endword_detector.is_end(user_text):
            reply_text = "好的，下次再见。"
        else:
            reply_text = deepseek.chat(user_text)

        logger.info(f"AI回复文本：{reply_text}")
        tts_file = tts.synthesize(reply_text)
        if tts_file:
            play_audio(tts_file)
        else:
            logger.error("TTS 生成语音失败。")

    # 唤醒循环
    detector = WakewordDetector()
    detector.start(on_wake)

if __name__ == "__main__":
    main()
