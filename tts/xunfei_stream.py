import websocket
import hashlib
import base64
import hmac
import json
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import threading
import numpy as np
import sounddevice as sd

class XunfeiTTSStream:
    def __init__(self, app_id, api_key, api_secret, vcn="x4_yezi",
                 speed=50, volume=50, pitch=50):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.vcn = vcn
        self.speed = speed
        self.volume = volume
        self.pitch = pitch
        self.aue = "raw"    # PCM流
        self.auf = "audio/L16;rate=16000"
        self.sfl = 1

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
        url = url + '?' + '&'.join([f"{k}={v[k]}" for k in v])
        return url

    def synthesize_stream(self, text, samplerate=16000, channels=1):
        """
        流式合成+边收边播报（仅PCM）。
        """
        self._error = None
        self._finished = threading.Event()

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                code = msg["code"]
                audio = base64.b64decode(msg["data"]["audio"])
                status = msg["data"]["status"]
                if code != 0:
                    print(f"讯飞TTS错误: code={code}, msg={msg.get('message')}")
                    self._error = msg.get('message')
                    ws.close()
                else:
                    # PCM播放，每次都播一帧
                    arr = np.frombuffer(audio, dtype=np.int16)
                    sd.play(arr, samplerate=samplerate)
                    sd.wait()
                if status == 2:
                    ws.close()
                    self._finished.set()
            except Exception as e:
                print("TTS流播放错误:", e)
                self._error = str(e)
                ws.close()
                self._finished.set()

        def on_error(ws, error):
            print("TTS WS 错误:", error)
            self._error = str(error)
            self._finished.set()

        def on_close(ws, *args):
            print("TTS WS 关闭")
            self._finished.set()

        def on_open(ws):
            def run(*args):
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
                        "text": base64.b64encode(text.encode('utf-8')).decode("utf-8")
                    }
                }
                ws.send(json.dumps(d))
            threading.Thread(target=run).start()

        ws_url = self._create_url()
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        self._finished.wait()
        if self._error:
            raise RuntimeError(f"TTS流式失败: {self._error}")
