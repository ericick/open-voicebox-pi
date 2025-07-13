import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import threading

class XunfeiTTSStream:
    def __init__(self, app_id, api_key, api_secret, vcn="x4_yezi",
                 aue="raw", auf="audio/L16;rate=16000", sfl=1, speed=50,
                 volume=50, pitch=50):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.vcn = vcn
        self.aue = aue
        self.auf = auf
        self.sfl = sfl
        self.speed = speed
        self.volume = volume
        self.pitch = pitch

    def _create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: tts-api.xfyun.cn\n"
        signature_origin += f"date: {date}\n"
        signature_origin += "GET /v2/tts HTTP/1.1"
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        v = {
            "authorization": authorization,
            "date": date,
            "host": "tts-api.xfyun.cn"
        }
        url = url + '?' + urlencode(v)
        return url

    def synthesize_stream(self, text):
        """
        生成器：每次 yield 一帧 PCM 音频数据（bytes），最后自动结束
        """
        ws_url = self._create_url()
        audio_queue = []
        done = threading.Event()
        error = []

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                code = msg["code"]
                if code != 0:
                    error.append(msg.get("message", "未知错误"))
                    done.set()
                    ws.close()
                    return
                audio = base64.b64decode(msg["data"]["audio"])
                status = msg["data"]["status"]
                audio_queue.append(audio)
                if status == 2:
                    done.set()
                    ws.close()
            except Exception as e:
                error.append(f"解析TTS返回时异常: {e}")
                done.set()
                ws.close()

        def on_error(ws, err):
            error.append(f"TTS websocket错误: {err}")
            done.set()
            ws.close()

        def on_close(ws, *args):
            done.set()

        def on_open(ws):
            def run(*_):
                d = {
                    "common": {"app_id": self.app_id},
                    "business": {
                        "aue": self.aue,
                        "auf": self.auf,
                        "vcn": self.vcn,
                        "tte": "utf8",
                        "sfl": self.sfl,
                        "speed": self.speed,
                        "volume": self.volume,
                        "pitch": self.pitch
                    },
                    "data": {
                        "status": 2,
                        "text": str(base64.b64encode(text.encode('utf-8')), "utf8")
                    }
                }
                ws.send(json.dumps(d))
            threading.Thread(target=run).start()

        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open

        threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}}).start()

        # 每收到一帧就yield，done后退出
        while not done.is_set() or audio_queue:
            if audio_queue:
                yield audio_queue.pop(0)
            else:
                time.sleep(0.01)
        if error:
            raise RuntimeError("讯飞TTS流式合成异常：" + "; ".join(error))

