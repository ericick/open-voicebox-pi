import hashlib
import base64
import time
import json
import requests
import tempfile
import soundfile as sf
from utils.logger import logger
from utils.retry_utils import retry

class XunfeiASR:
    def __init__(self, app_id, api_key, api_secret, hotwords=None):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = "https://iat-api.xfyun.cn/v2/iat"
        self.engine_type = "sms16k"
        self.aue = "raw"
        self.hotwords = hotwords or ""

    def get_auth_params(self, audio_len):
        cur_time = str(int(time.time()))
        param = {
            "engine_type": self.engine_type,
            "aue": self.aue,
            "audio_len": audio_len
        }
        if self.hotwords:
            param["word"] = self.hotwords
        x_param = base64.b64encode(json.dumps(param).encode("utf-8")).decode("utf-8")
        m2 = hashlib.md5()
        m2.update((self.api_key + cur_time + x_param).encode('utf-8'))
        x_checksum = m2.hexdigest()
        headers = {
            "X-Appid": self.app_id,
            "X-CurTime": cur_time,
            "X-Param": x_param,
            "X-CheckSum": x_checksum,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"
        }
        return headers

    @retry(max_attempts=3, wait=2, exceptions=(requests.RequestException, ), msg="ASR网络请求异常，重试")
    def recognize(self, audio_data, samplerate=16000):
        if isinstance(audio_data, bytes):
            audio_bytes = audio_data
        else:
            with tempfile.NamedTemporaryFile(suffix=".pcm", delete=True) as tmpfile:
                sf.write(tmpfile.name, audio_data, samplerate, subtype='PCM_16')
                with open(tmpfile.name, 'rb') as f:
                    audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        headers = self.get_auth_params(audio_len=len(audio_bytes))
        data = {"audio": audio_b64}
        try:
            resp = requests.post(self.url, headers=headers, data=data, timeout=10)
            result = resp.json()
            logger.info(f"讯飞ASR原始返回：{result}")
            if result.get("code") != 0:
                logger.error(f"讯飞ASR出错：{result.get('desc')}")
                return ""
            text = ""
            for ws in result["data"]["result"]["ws"]:
                for cw in ws["cw"]:
                    text += cw["w"]
            logger.info(f"讯飞ASR最终识别文本：{text}")
            return text.strip()
        except Exception as e:
            logger.error(f"讯飞ASR API异常: {e}")
            return ""
