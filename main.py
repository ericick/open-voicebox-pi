import os
from wakeword.porcupine_adapter import WakewordDetector
from audio_in.recorder import Recorder
from asr.xunfei_asr import XunfeiASR
from dialogue.deepseek_adapter import DeepseekAdapter
from tts.xunfei_adapter import XunfeiTTS
from audio_out.player import play_audio
from endword.endword_detector import EndwordDetector
from utils.config_loader import load_config
from utils.logger import logger

WELCOME_AUDIO_PATH = "audio_out/welcome.mp3"
WELCOME_TEXT = "你好。"

def prepare_welcome_audio(tts):
    """
    检查本地欢迎语音是否存在，如无则用TTS生成保存。
    """
    if not os.path.exists(WELCOME_AUDIO_PATH):
        logger.info("未发现本地欢迎语音，将使用TTS生成。")
        tts.synthesize(WELCOME_TEXT, out_file=WELCOME_AUDIO_PATH)
    else:
        logger.info("本地欢迎语音已存在，直接复用。")

def main():
    config = load_config()
    hotwords = config["xunfei_asr"].get("hotwords", "")

    recorder = Recorder()
    asr = XunfeiASR(
        app_id=config["xunfei_asr"]["app_id"],
        api_key=config["xunfei_asr"]["api_key"],
        api_secret=config["xunfei_asr"]["api_secret"],
        hotwords=hotwords
    )
    deepseek = DeepseekAdapter(api_key=config["deepseek"]["api_key"])
    tts = XunfeiTTS(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"]
    )
    endword_detector = EndwordDetector(keywords=config["endwords"])

    # 可选：全局会话历史（多轮对话）
    conversation_history = []

    # 启动时准备本地欢迎语音
    prepare_welcome_audio(tts)

    def on_wake():
        nonlocal conversation_history
        try:
            # 1. 唤醒后立即本地播放欢迎语音
            play_audio(WELCOME_AUDIO_PATH)
            logger.info("唤醒成功，准备录音。")
            audio = recorder.record()
            if audio is None or len(audio) == 0:
                logger.warning("未录到有效语音。")
                tts_file = tts.synthesize("未检测到有效语音，请再试一次。")
                if tts_file:
                    play_audio(tts_file)
                return

            user_text = asr.recognize(audio)
            logger.info(f"语音识别结果：{user_text}")

            if not user_text.strip():
                reply_text = "我没有听清，你可以再说一遍吗？"
                # 没听清不记入上下文
            elif endword_detector.is_end(user_text):
                reply_text = "好的，下次再见。"
                conversation_history.clear()
            else:
                # 加入历史上下文
                conversation_history.append({"role": "user", "content": user_text})
                reply_text = deepseek.chat(context=conversation_history)
                conversation_history.append({"role": "assistant", "content": reply_text})

            logger.info(f"AI回复文本：{reply_text}")
            tts_file = tts.synthesize(reply_text)
            if tts_file:
                play_audio(tts_file)
            else:
                logger.error("TTS 生成语音失败。")
        except Exception as e:
            logger.error(f"主流程异常：{e}")
            tts_file = tts.synthesize("系统发生错误，请稍后重试。")
            if tts_file:
                play_audio(tts_file)

    detector = WakewordDetector()
    detector.start(on_wake)

if __name__ == "__main__":
    main()
