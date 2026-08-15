import os
import re
import time
from utils.initializer import ensure_initialized
from asr.xunfei_asr import XunfeiASR
from dialogue.codex_adapter import CodexAdapter
from dialogue.deepseek_adapter import DeepseekAdapter
from dialogue.router import DialogueRouter
from tts.xunfei_stream import XunfeiTTSStream
from audio_out.player import play_audio, play_audio_stream, wait_until_idle
from endword.endword_detector import EndwordDetector
from audio_in.recorder import Recorder
from utils.config_loader import load_config
from utils.logger import logger
from utils.audio_device import DeviceUnavailable
from wakeword.wakeword_detector import WakewordDetector


def clean_for_speech(text):
    """去掉不适合朗读的符号（markdown/星号/列表符等），压缩空白。"""
    text = re.sub(r"[*#`>_~\[\](){}]", "", text)
    text = re.sub(r"^\s*[-•·]\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main():
    logger.info("==== 智能语音音箱主流程启动 ====")
    config = load_config()
    logger.debug(f"完整配置参数: {config}")

    welcome_audio_path = config.get("welcome_audio_path", "audio_out/welcome.mp3")
    # 幂等初始化：缺少的欢迎音/错误提示音会自动生成，已存在的跳过
    ensure_initialized(config)

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
        system_prompt=config["deepseek"].get("system_prompt", ""),
        web_search=config["deepseek"].get("web_search", False)
    )
    codex_cfg = config.get("codex", {})
    codex = CodexAdapter(
        model=codex_cfg.get("model", "deepseek-v4-flash"),
        provider=codex_cfg.get("provider", "deepseek"),
        system_prompt=config["deepseek"].get("system_prompt", ""),
        timeout_s=codex_cfg.get("timeout_s", 120),
    )
    dialogue = DialogueRouter(
        default_adapter=deepseek,
        codex_adapter=codex,
        enabled=codex_cfg.get("enabled", False),
        triggers=codex_cfg.get("triggers", []),
        min_length=codex_cfg.get("min_length", 40),
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
    recorder = Recorder(
        samplerate=config["audio_in"]["samplerate"],
        channels=config["audio_in"]["channels"],
        dtype=config["audio_in"]["dtype"],
        block_size=config["audio_in"]["block_size"],
        max_record_time=config["audio_in"]["max_record_time"],
        silence_threshold=config["audio_in"].get("silence_threshold", 2000),
        silence_duration=config["audio_in"].get("silence_duration", 2.0),
        device=config["audio_in"]["device"],
    )

    conversation_history = []

    output_device = config.get("audio_out", {}).get("device")

    tts_cache_dir=config["tts_cache_dir"]
    def play_standard_error(tag):
        err_file = os.path.join(tts_cache_dir, f"{tag}.mp3")
        if os.path.exists(err_file):
            play_audio(err_file, device=output_device)
        else:
            play_audio(os.path.join(tts_cache_dir, "error_system.mp3"), device=output_device)

    def on_wakeword_detected():
        try:
            play_audio(config["welcome_audio_path"], device=output_device)
            logger.info("已唤醒，进入多轮对话...")
            blank_count = 1
    
            while True:   # 增加循环
                # 等音箱把话说完再开始下一轮录音，避免录到自己
                wait_until_idle(timeout_s=60)
                audio_blocks = recorder.record_stream()
                user_text = asr.recognize_stream(audio_blocks)
                logger.info(f"用户语音识别结果: {user_text}")
    
                if not user_text.strip():
                    logger.debug("识别结果为空，提示用户重说。")
                    play_standard_error("error_no_input")
                    time.sleep(0.3)
                    if blank_count == 1:
                        blank_count += 1
                        continue    # 让用户重说
                    else:
                        blank_count = 1
                        break    # 多次为空直接退出
    
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
                    farewell_text = clean_for_speech(farewell_text)
                    audio_gen = tts_stream.synthesize_stream(farewell_text)
                    play_audio_stream(audio_gen, device=output_device, samplerate=44100, channels=2, dtype='int16')
                    conversation_history.clear()
                    break       # 跳出多轮对话，回到唤醒监听
    
                else:
                    logger.debug("进入多轮对话处理。")
                    conversation_history.append({"role": "user", "content": user_text})
                    reply_text = dialogue.chat(context=conversation_history)
                    conversation_history.append({"role": "assistant", "content": reply_text})
                    logger.info(f"AI回复文本: {reply_text}")
                    reply_text = clean_for_speech(reply_text)
                    audio_gen = tts_stream.synthesize_stream(reply_text)
                    play_audio_stream(audio_gen, device=output_device, samplerate=44100, channels=2, dtype='int16')
                    
        except DeviceUnavailable as e:
            logger.warning(f"录音设备不可用：{e}")
            play_standard_error("error_recording")
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
        "model_dir": wake_cfg["model_dir"],
        "keywords_file": wake_cfg.get(
            "keywords_file",
            os.path.join(wake_cfg["model_dir"], "keywords_custom.txt"),
        ),
        "audio_device_index": wake_cfg.get("audio_device_index"),
        "channels": config["audio_in"]["channels"],
        "keywords_score": wake_cfg.get("keywords_score", 1.0),
        "keywords_threshold": wake_cfg.get("keywords_threshold", 0.25),
        "num_threads": wake_cfg.get("num_threads", 2),
    }
    wakeword_detector = WakewordDetector(**args)

    # 启动唤醒词监听，检测到后进入对话主流程
    while True:
        wakeword_detector.start(on_wakeword_detected)


if __name__ == "__main__":
    main()
