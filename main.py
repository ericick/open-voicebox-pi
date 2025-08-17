import os
from utils.initializer import ensure_initialized
from asr.xunfei_asr import XunfeiASR
from dialogue.deepseek_adapter import DeepseekAdapter
from tts.xunfei_stream import XunfeiTTSStream
from audio_out.player import play_audio, play_audio_stream
from endword.endword_detector import EndwordDetector
from audio_in.recorder import Recorder
from utils.config_loader import load_config
from utils.logger import logger
from wakeword.porcupine_adapter import WakewordDetector

def main():
    logger.info("==== 智能语音音箱主流程启动 ====")
    config = load_config()
    logger.debug(f"完整配置参数: {config}")

    welcome_audio_path = config.get("welcome_audio_path", "audio_out/welcome.mp3")
    need_init = not os.path.exists(welcome_audio_path)
    if need_init:
        ensure_initialized(config)
    else:
        logger.info("欢迎语音和报错音频均已存在，无需初始化。")

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
    tts_stream = XunfeiTTSStream(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"],
        vcn=config["xunfei"].get("vcn", "x4_yezi"),
        speed=config["xunfei"].get("speed", 50),
        volume=config["xunfei"].get("volume", 50),
        pitch=config["xunfei"].get("pitch", 50)
    )
    endword_detector = EndwordDetector(keywords=config["endwords"])
    recorder = Recorder(device=1, channels=6)

    conversation_history = []

    tts_cache_dir=config["tts_cache_dir"]
    def play_standard_error(tag):
        err_file = os.path.join(tts_cache_dir, f"{tag}.mp3")
        if os.path.exists(err_file):
            play_audio(err_file)
        else:
            play_audio(os.path.join(tts_cache_dir, "error_system.mp3"))

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
                    tmp_context = conversation_history + [{"role": "user", "content": user_text}]
                    tmp_context.append({
                        "role": "user",
                        "content": "请根据以上整段对话，用一句自然、简短的中文结束语向我告别。不要提出新问题，不要额外延伸。"
                    })
                    farewell_text = deepseek.chat(context=tmp_context).strip()
                    if not farewell_text:
                        farewell_text = "好的，下次再见。"
                    audio_gen = tts_stream.synthesize_stream(farewell_text)
                    play_audio_stream(audio_gen, device=2, samplerate=44100, channels=2, dtype='int16')
                    conversation_history.clear()
                    break       # 跳出多轮对话，回到唤醒监听
    
                else:
                    logger.debug("进入多轮对话处理。")
                    conversation_history.append({"role": "user", "content": user_text})
                    reply_text = deepseek.chat(context=conversation_history)
                    conversation_history.append({"role": "assistant", "content": reply_text})
                    logger.info(f"AI回复文本: {reply_text}")
                    audio_gen = tts_stream.synthesize_stream(reply_text)
                    play_audio_stream(audio_gen, device=2, samplerate=44100, channels=2, dtype='int16')
                    
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
