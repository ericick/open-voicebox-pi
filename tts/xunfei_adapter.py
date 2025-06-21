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
import _thread as thread
import os
import logging

logger = logging.getLogger("XunfeiTTS")
logger.setLevel(logging.INFO)

class XunfeiTTS:
    def __init__(self, app_id, api_key, api_secret, vcn="x4_yezi",
                 aue="lame", auf="audio/L16;rate=16000", sfl=1, speed=50,
                 volume=50, pitch=50, tts_out_dir="audio_out", log_dir="tts_log"):
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
        self.tts_out_dir = tts_out_dir
        os.makedirs(self.tts_out_dir, exist_ok=True)
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

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

    def synthesize(self, text, filename_prefix="tts"):
        self._result_audio = []
        self._error = None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        def on_message(ws, message):
            try:
                msg = json.loads(message)
                code = msg["code"]
                sid = msg.get("sid", "unknown")
                audio = base64.b64decode(msg["data"]["audio"])
                status = msg["data"]["status"]
                logger.debug(f"XunfeiTTS on_message: sid={sid}, code={code}, status={status}")
                if code != 0:
                    errMsg = msg.get("message", "未知错误")
                    logger.error(f"讯飞TTS错误 [sid:{sid} code:{code}] {errMsg}")
                    self._error = f"讯飞TTS错误 [sid:{sid} code:{code}] {errMsg}"
                    ws.close()
                else:
                    self._result_audio.append(audio)
                if status == 2:
                    logger.info("讯飞TTS流式音频全部接收完毕")
                    ws.close()
            except Exception as e:
                logger.error(f"接收TTS音频时异常: {e}")

        def on_error(ws, error):
            logger.error(f"WebSocket 错误: {error}")
            self._error = f"WebSocket 错误: {error}"

        def on_close(ws, close_status_code, close_msg):
            logger.info("WebSocket 连接关闭")

        def on_open(ws):
            def run(*args):
                try:
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
                            "text": str(base64.b64encode(text.encode('utf-8')), "UTF8")
                        }
                    }
                    ws.send(json.dumps(d))
                    logger.info(f"已发送TTS合成请求：{d}")
                except Exception as e:
                    logger.error(f"TTS ws.send异常: {e}")
                    self._error = f"TTS ws.send异常: {e}"
                    ws.close()
            thread.start_new_thread(run, ())

        ws_url = self._create_url()
        logger.debug(f"WebSocket URL: {ws_url}")
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        ws.on_open = on_open

        logger.info("开始流式TTS WebSocket连接")
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        if self._error:
            raise RuntimeError(self._error)

        if self._result_audio:
            out_file = os.path.join(self.tts_out_dir, f"{filename_prefix}_{timestamp}.mp3")
            with open(out_file, 'wb') as f:
                for chunk in self._result_audio:
                    f.write(chunk)
            logger.info(f"TTS合成音频已保存为 {out_file}")
            return out_file
        else:
            logger.error("未收到任何音频数据")
            raise RuntimeError("讯飞TTS合成失败，未收到音频")

