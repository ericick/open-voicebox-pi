import os
from tts.xunfei_adapter import XunfeiTTS
from utils.logger import logger
from utils.tts_cache_manager import TTSCacheManager

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
    tts_cache_manager = TTSCacheManager(
        tts=tts,
        tts_cache_dir=tts_cache_dir,
        error_prompts=config.get("error_prompts", {})
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

    # 4. 检查所有 error_prompts 音频
    tts_cache_manager.prepare_error_prompts()

    logger.info("音频初始化完毕。")
    # 你可以返回需要用到的路径（可选）
    return {
        "tts": tts,
        "tts_cache_manager": tts_cache_manager,
        "welcome_audio_path": welcome_audio_path,
        "audio_out_dir": audio_out_dir,
        "tts_cache_dir": tts_cache_dir
    }
