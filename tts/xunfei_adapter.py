import hashlib
import base64
import time
import json
import requests
from utils.logger import logger

class XunfeiTTS:
    def __init__(self, app_id, api_key, api_secret):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = "https://tts-api.xfyun.cn/v2/tts"
        self.voice_name = "xiaoyan"  # 可在官网查可选发音人

    def get_auth_params(self, text):
        cur_time = str(int(time.time()))
        params = {"aue": "lame", "voice_name": self.voice_name, "speed": 50, "volume": 50, "pitch": 50, "engine_type": "intp65"}
        x_param = base64.b64encode(json.dumps(params).encode("utf-8")).decode("utf-8")
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

    def synthesize(self, text, out_file="response.mp3"):
        headers = self.get_auth_params(text)
        data = {"text": text}
        try:
            response = requests.post(self.url, headers=headers, data=data, timeout=10)
            if response.headers['Content-Type'] == "audio/mpeg":
                with open(out_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"讯飞TTS语音已保存: {out_file}")
                return out_file
            else:
                logger.error(f"讯飞TTS API失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"讯飞TTS接口异常: {e}")
            return None
