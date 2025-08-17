import os
from tts.xunfei_adapter import XunfeiTTS
from utils.logger import logger

def ensure_initialized(config):
    """
    初始化欢迎音频和所有错误提示音频（如本地不存在则生成），所有内容从 config 读取。
    """
    # 1. 确保输出目录存在
    audio_out_dir = config.get("audio_out_dir", "audio_out")
    tts_cache_dir = config.get("tts_cache_dir", "audio_out/tts_cache")
    os.makedirs(audio_out_dir, exist_ok=True)
    os.makedirs(tts_cache_dir, exist_ok=True)

    # 2. 初始化 TTS 和缓存管理器
    tts = XunfeiTTS(
        app_id=config["xunfei"]["app_id"],
        api_key=config["xunfei"]["api_key"],
        api_secret=config["xunfei"]["api_secret"],
        vcn=config["xunfei"].get("vcn", "x4_yezi"),
        speed=config["xunfei"].get("speed", 50),
        volume=config["xunfei"].get("volume", 50),
        pitch=config["xunfei"].get("pitch", 50),
        tts_out_dir=audio_out_dir
    )

    # 3. 检查欢迎音频
    welcome_audio_path = config.get("welcome_audio_path", "audio_out/welcome.mp3")
    if not os.path.exists(welcome_audio_path):
        welcome_text = config.get("welcome_text", "你好，我是智能语音助手。")
        logger.info("未发现本地欢迎语音，将用TTS生成。")
        welcome_file = tts.synthesize(welcome_text, filename_prefix="welcome")
        os.replace(welcome_file, welcome_audio_path)
        logger.info(f"欢迎语音生成并保存到：{welcome_audio_path}")
    else:
        logger.debug(f"本地欢迎语音已存在：{welcome_audio_path}")
    
    # 3. 检查欢迎音频
    error_prompts = config.get("error_prompts", {})
    for tag, text in error_prompts.items():
        out_path = os.path.join(tts_cache_dir, f"{tag}.mp3")
        if os.path.exists(out_path):
            logger.debug(f"[跳过] 错误提示音已存在：{out_path}")
            continue
        try:
            logger.info(f"生成错误提示音：{tag}")
            tmp_file = tts.synthesize(text, filename_prefix=f"err_{tag}")
            os.replace(tmp_file, out_path)
            logger.info(f"错误提示音已生成：{out_path}")
        except Exception as e:
            logger.error(f"生成错误提示音失败（{tag}）：{e}")

    logger.info("初始化完成：欢迎音与错误提示音就绪。")
