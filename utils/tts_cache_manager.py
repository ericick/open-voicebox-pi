import os
import glob
import time
import hashlib
from utils.logger import logger

class TTSCacheManager:
    def __init__(self, tts, tts_cache_dir, error_prompts):
        self.tts = tts
        self.tts_cache_dir = tts_cache_dir
        self.error_prompts = error_prompts

        if not os.path.isdir(self.tts_cache_dir):
            os.makedirs(self.tts_cache_dir, exist_ok=True)

    def cache_filepath(self, tag):
        return os.path.join(self.tts_cache_dir, f"{tag}.mp3")

    def prepare_error_prompts(self):
        for tag, text in self.error_prompts.items():
            fpath = self.cache_filepath(tag)
            if not os.path.exists(fpath):
                logger.info(f"生成TTS缓存：{tag} -> {text}")
                # 合成到tts_out_dir，生成临时文件
                tmp_audio = self.tts.synthesize(text, filename_prefix=tag)
                os.replace(tmp_audio, fpath)
                logger.info(f"TTS缓存已生成并移动到：{fpath}")
            else:
                logger.debug(f"TTS缓存已存在：{fpath}")

    def get_error_audio(self, tag):
        fpath = self.cache_filepath(tag)
        if os.path.exists(fpath):
            return fpath
        else:
            logger.error(f"未找到TTS错误提示缓存：{fpath}")
            return None

    def cache_normal_tts(self, text):
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        fpath = os.path.join(self.tts_cache_dir, f"normal_{h}.mp3")
        if not os.path.exists(fpath):
            tmp_path = self.tts.synthesize(text, filename_prefix=f"normal_{h}")
            os.replace(tmp_path, fpath)
        return fpath

    def clean_cache(self, max_files=50, max_bytes=100*1024*1024):
        files = glob.glob(os.path.join(self.tts_cache_dir, "*.mp3"))
        files = [(f, os.path.getmtime(f), os.path.getsize(f)) for f in files]
        files.sort(key=lambda x: x[1], reverse=True)
        total = 0
        for i, (f, _, size) in enumerate(files):
            total += size
            if i >= max_files or total > max_bytes:
                logger.info(f"清理过期TTS缓存：{f}")
                os.remove(f)
