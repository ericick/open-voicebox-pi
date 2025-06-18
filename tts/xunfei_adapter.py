import os
import base64
import hashlib
import json
import time
import requests
from utils.logger import logger

class XunfeiTTS:
    def __init__(self, app_id, api_key, api_secret, voice_name="xiaoyan", speed=50, volume=50, pitch=50, engine_type="intp65", tts_out_dir="audio_out"):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.voice_name = voice_name
        self.speed = speed
        self.volume = volume
        self.pitch = pitch
        self.engine_type = engine_type
        self.aue = "lame"  # mp3
        self.url = "https://tts-api.xfyun.cn/v2/tts"
        self.tts_out_dir = tts_out_dir
        if not os.path.exists(self.tts_out_dir):
            os.makedirs(self.tts_out_dir, exist_ok=True)

    def get_auth_headers(self, text_len=0):
        cur_time = str(int(time.time()))
        params = {
            "aue": self.aue,
            "voice_name": self.voice_name,
            "speed": str(self.speed),
            "volume": str(self.volume),
            "pitch": str(self.pitch),
            "engine_type": self.engine_type,
            "text_type": "text"
        }
        param_str = base64.b64encode(json.dumps(params).encode("utf-8")).decode("utf-8")
        m = hashlib.md5()
        m.update((self.api_key + cur_time + param_str).encode("utf-8"))
        checksum = m.hexdigest()
        headers = {
            "X-Appid": self.app_id,
            "X-CurTime": cur_time,
            "X-Param": param_str,
            "X-CheckSum": checksum,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        return headers

    def _synthesize_single(self, text, out_file=None):
        """合成单段文本，并写入mp3"""
        data = {"text": text}
        headers = self.get_auth_headers(len(text))
        try:
            resp = requests.post(self.url, headers=headers, data=data, timeout=10)
            content_type = resp.headers.get("Content-Type", "")
            if "audio/mpeg" in content_type or "audio/mp3" in content_type:
                audio = resp.content
                if out_file is None:
                    ts = int(time.time() * 1000)
                    out_file = os.path.join(self.tts_out_dir, f"tts_{ts}.mp3")
                with open(out_file, "wb") as f:
                    f.write(audio)
                logger.info(f"TTS合成成功: {out_file}")
                return out_file
            else:
                # 失败时返回json
                try:
                    err = resp.json()
                except Exception:
                    err = {"desc": resp.text}
                logger.error(f"TTS接口错误: {err}")
                raise RuntimeError(f"TTS合成失败: {err}")
        except Exception as e:
            logger.error(f"TTS单段合成异常: {e}")
            raise

    def synthesize(self, text, out_file=None):
        """
        自动分段TTS合成，最大300字一段，超长文本自动切分，多段合成后拼接（拼接留给主流程/播放器）。
        返回最终合成的mp3路径（如多段返回主文件路径，单段返回单文件路径）。
        """
        MAX_BYTES = 300  # 单段最大长度，UTF-8字节
        text_bytes = text.encode("utf-8")
        if len(text_bytes) <= MAX_BYTES:
            return self._synthesize_single(text, out_file=out_file)

        # 自动分段，优先按句号/逗号等切分，最大每段<=300字节
        logger.info("TTS文本过长，自动分段合成")
        segs = []
        curr = ""
        for ch in text:
            curr += ch
            if len(curr.encode("utf-8")) >= MAX_BYTES or ch in "。！？!?,，. ":
                segs.append(curr)
                curr = ""
        if curr:
            segs.append(curr)

        logger.debug(f"TTS切分后共{len(segs)}段")
        ts = int(time.time() * 1000)
        base = os.path.splitext(out_file or f"tts_{ts}.mp3")[0]
        audio_files = []
        for i, seg in enumerate(segs):
            part_file = f"{base}_part{i}.mp3"
            try:
                self._synthesize_single(seg, out_file=part_file)
                audio_files.append(part_file)
            except Exception as e:
                logger.error(f"TTS分段合成第{i+1}段失败: {e}")
                # 这里决定是否继续，或抛出中止
                raise

        # 合并所有片段为一个mp3
        try:
            from pydub import AudioSegment
            merged = AudioSegment.empty()
            for f in audio_files:
                merged += AudioSegment.from_mp3(f)
            final_path = out_file or os.path.join(self.tts_out_dir, f"tts_{ts}_full.mp3")
            merged.export(final_path, format="mp3")
            logger.info(f"TTS多段合成并拼接成功: {final_path}")
            # 清理分段文件
            for f in audio_files:
                try:
                    os.remove(f)
                except Exception:
                    logger.warning(f"删除临时分段失败: {f}")
            return final_path
        except ImportError:
            logger.error("未安装pydub，无法自动拼接mp3。仅返回首段音频文件")
            return audio_files[0] if audio_files else None
        except Exception as e:
            logger.error(f"TTS多段合成拼接失败: {e}")
            return audio_files[0] if audio_files else None

