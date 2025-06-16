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
from utils.tts_cache_manager import TTSCacheManager

def prepare_welcome_audio(tts, welcome_text, welcome_audio_path):
    if not os.path.exists(welcome_audio_path):
        logger.info("未发现本地欢迎语音，将使用TTS生成。")
        tts.synthesize(welcome_text, out_file=welcome_audio_path)
    else:
        logger.debug(f"本地欢迎语音已存在：{welcome_audio_path}")

def main():
    logger.info("==== 语音音箱主程序启动 ====")
    config = load_config()
    logger.debug(f"完整配置参数: {config}")

    tts = XunfeiTTS(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"],
        voice_name=config["xunfei"].get("voice_name", "xiaoyan"),
        speed=config["xunfei"].get("speed", 50),
        volume=config["xunfei"].get("volume", 50),
        pitch=config["xunfei"].get("pitch", 50),
        engine_type=config["xunfei"].get("engine_type", "intp65"),
        tts_out_dir=config.get("audio_out_dir", "audio_out")
    )

    tts_cache_manager = TTSCacheManager(
        tts=tts,
        tts_cache_dir=config.get("tts_cache_dir", "audio_out/tts_cache"),
        error_prompts=config.get("error_prompts", {})
    )
    prepare_welcome_audio(tts, config["welcome_text"], config["welcome_audio_path"])
    tts_cache_manager.prepare_error_prompts()
    tts_cache_manager.clean_cache(max_files=50, max_bytes=100*1024*1024)

    recorder = Recorder()
    asr = XunfeiASR(
        app_id=config["xunfei_asr"]["app_id"],
        api_key=config["xunfei_asr"]["api_key"],
        api_secret=config["xunfei_asr"]["api_secret"],
        hotwords=config["xunfei_asr"].get("hotwords", ""),
        engine_type=config["xunfei_asr"].get("engine_type", "sms16k"),
    )
    deepseek = DeepseekAdapter(
        api_key=config["deepseek"]["api_key"],
        api_url=config["deepseek"].get("api_url", "https://api.deepseek.com/v1/chat/completions"),
        model=config["deepseek"].get("model", "deepseek-chat"),
        temperature=config["deepseek"].get("temperature", 0.7),
        max_tokens=config["deepseek"].get("max_tokens", 2048)
    )
    endword_detector = EndwordDetector(keywords=config["endwords"])

    wakeword_config = config.get("wakeword", {})
    keyword_paths = wakeword_config.get("keyword_paths", ["wakeword/xiaozhu_xiaozhu.ppn"])
    access_key = wakeword_config.get("access_key", "")
    sensitivities = wakeword_config.get("sensitivities", [0.7]*len(keyword_paths))
    audio_device_index = wakeword_config.get("audio_device_index", None)

    conversation_history = []

    def play_standard_error(tag):
        audio = tts_cache_manager.get_error_audio(tag)
        if audio:
            play_audio(audio)
        else:
            play_audio(tts_cache_manager.get_error_audio("error_system"))

    def on_wake():
        nonlocal conversation_history
        try:
            play_audio(config["welcome_audio_path"])
            logger.info("【主流程】唤醒成功，开始录音。")
            audio = recorder.record()
            if audio is None or len(audio) == 0:
                logger.warning("未录到有效语音。")
                play_standard_error("error_no_input")
                return

            logger.info("【主流程】录音结束，开始语音识别。")
            user_text = asr.recognize(audio)
            logger.info(f"【主流程】语音识别结果: {user_text}")

            if not user_text.strip():
                logger.debug("【分支】识别结果为空，提示用户重说。")
                play_standard_error("error_no_input")
                return
            elif endword_detector.is_end(user_text):
                logger.info("【分支】检测到结束词，清空历史对话。")
                reply_text = "好的，下次再见。"
                conversation_history.clear()
            else:
                logger.debug("【分支】进入多轮对话处理。")
                conversation_history.append({"role": "user", "content": user_text})
                reply_text = deepseek.chat(context=conversation_history)
                conversation_history.append({"role": "assistant", "content": reply_text})

            logger.info(f"【主流程】AI回复文本: {reply_text}")
            tts_file = tts_cache_manager.cache_normal_tts(reply_text)
            if tts_file:
                play_audio(tts_file)
            else:
                play_standard_error("error_tts")
        except Exception as e:
            logger.error(f"主流程异常：{e}")
            import traceback
            tb = traceback.format_exc()
            if "audio" in tb or "sounddevice" in tb:
                play_standard_error("error_recording")
            elif "requests" in tb and "ASR" in tb:
                play_standard_error("error_asr")
            elif "ConnectionError" in tb or "network" in tb:
                play_standard_error("error_network")
            elif "TTS" in tb:
                play_standard_error("error_tts")
            else:
                play_standard_error("error_system")

    detector = WakewordDetector(
        keyword_paths=keyword_paths,
        access_key=access_key,
        sensitivities=sensitivities,
        audio_device_index=audio_device_index
    )
    detector.start(on_wake)

if __name__ == "__main__":
    main()
