import os
from asr.xunfei_asr import XunfeiASR
from dialogue.deepseek_adapter import DeepseekAdapter
from tts.xunfei_adapter import XunfeiTTS
from audio_out.player import play_audio
from endword.endword_detector import EndwordDetector
from audio_in.recorder import Recorder
from utils.config_loader import load_config
from utils.logger import logger
from utils.tts_cache_manager import TTSCacheManager
from wakeword.porcupine_adapter import WakewordDetector

def prepare_welcome_audio(tts, welcome_text, welcome_audio_path):
    if not os.path.exists(welcome_audio_path):
        logger.info("未发现本地欢迎语音，将使用TTS生成。")
        # 合成welcome音频，存到tts_out_dir下
        generated_audio_path = tts.synthesize(welcome_text, filename_prefix="welcome")
        # 用os.replace移动到你指定的位置
        os.replace(generated_audio_path, welcome_audio_path)
        logger.info(f"欢迎语音生成并保存到：{welcome_audio_path}")
    else:
        logger.debug(f"本地欢迎语音已存在：{welcome_audio_path}")

def main():
    logger.info("==== 智能语音音箱主流程启动 ====")
    config = load_config()
    logger.debug(f"完整配置参数: {config}")

    tts = XunfeiTTS(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"],
        vcn=config["xunfei"].get("vcn", "x4_yezi"),
        speed=config["xunfei"].get("speed", 50),
        volume=config["xunfei"].get("volume", 50),
        pitch=config["xunfei"].get("pitch", 50),
        tts_out_dir=config.get("audio_out_dir", "audio_out")
    )

    tts_cache_manager = TTSCacheManager(
        tts=tts,
        tts_cache_dir=config.get("tts_cache_dir", "audio_out/tts_cache"),
        error_prompts=config.get("error_prompts", {})
    )
    prepare_welcome_audio(tts, config["welcome_text"], config["welcome_audio_path"])
    tts_cache_manager.prepare_error_prompts()

    cache_policy = config.get("tts_cache_policy", {})
    max_files = cache_policy.get("max_files", 50)
    max_bytes = cache_policy.get("max_bytes", 100*1024*1024)
    tts_cache_manager.clean_cache(max_files=max_files, max_bytes=max_bytes)

    asr = XunfeiASR(
        app_id=config["xunfei_asr"]["app_id"],
        api_key=config["xunfei_asr"]["api_key"],
        api_secret=config["xunfei_asr"]["api_secret"],
        hotwords=config["xunfei_asr"].get("hotwords", ""),
    )
    deepseek = DeepseekAdapter(
        api_key=config["deepseek"]["api_key"],
        base_url=config["deepseek"].get("api_url", "https://api.deepseek.com"),
        model=config["deepseek"].get("model", "deepseek-chat"),
        temperature=config["deepseek"].get("temperature", 0.7),
        max_tokens=config["deepseek"].get("max_tokens", 2048),
        system_prompt=config["deepseek"].get("system_prompt", "")
    )
    endword_detector = EndwordDetector(keywords=config["endwords"])
    recorder = Recorder(device=1, channels=6)

    conversation_history = []

    def play_standard_error(tag):
        audio = tts_cache_manager.get_error_audio(tag)
        if audio:
            play_audio(audio)
        else:
            play_audio(tts_cache_manager.get_error_audio("error_system"))

    def on_wakeword_detected():
        try:
            play_audio(config["welcome_audio_path"])
            logger.info("已唤醒，进入多轮对话...")
    
            while True:   # 增加循环
                audio_blocks = recorder.record_stream(max_record_time=10)
                user_text = asr.recognize_stream(audio_blocks)
                logger.info(f"用户语音识别结果: {user_text}")
    
                if not user_text.strip():
                    logger.debug("识别结果为空，提示用户重说。")
                    play_standard_error("error_no_input")
                    continue    # 让用户重说
    
                elif endword_detector.is_end(user_text):
                    logger.info("检测到结束词，清空历史对话。")
                    reply_text = "好的，下次再见。"
                    conversation_history.clear()
                    tts_file = tts_cache_manager.cache_normal_tts(reply_text)
                    if tts_file:
                        play_audio(tts_file)
                    else:
                        play_standard_error("error_tts")
                    break       # 跳出多轮对话，回到唤醒监听
    
                else:
                    logger.debug("进入多轮对话处理。")
                    conversation_history.append({"role": "user", "content": user_text})
                    reply_text = deepseek.chat(context=conversation_history)
                    conversation_history.append({"role": "assistant", "content": reply_text})
                    logger.info(f"AI回复文本: {reply_text}")
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
            elif "websocket" in tb and "ASR" in tb:
                play_standard_error("error_asr")
            elif "requests" in tb or "ConnectionError" in tb or "network" in tb:
                play_standard_error("error_network")
            elif "TTS" in tb:
                play_standard_error("error_tts")
            else:
                play_standard_error("error_system")


    # ==== 配置并启动唤醒词检测 ====
    wake_cfg = config["wakeword"]
    args = {
        "keyword_paths": wake_cfg["keyword_paths"],
        "access_key": wake_cfg["access_key"],
        "sensitivities": wake_cfg.get("sensitivities"),
        "model_path": wake_cfg.get("model_path"),
        "audio_device_index": wake_cfg.get("audio_device_index")
    }
    wakeword_detector = WakewordDetector(**args)

    # 启动唤醒词监听，检测到后进入对话主流程
    while True:
        wakeword_detector.start(on_wakeword_detected)


if __name__ == "__main__":
    main()
