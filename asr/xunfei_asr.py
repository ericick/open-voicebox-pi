import time
import json
import base64
import hashlib
import threading
import websocket
import ssl
import numpy as np
from utils.logger import logger

class XunfeiASR:
    def __init__(self, app_id, api_key, api_secret, hotwords="", engine_type="sms16k"):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.hotwords = hotwords
        self.engine_type = engine_type
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.result = ""
        self.result_lock = threading.Lock()
        self.finished = threading.Event()

    def _assemble_url(self):
        # 按官方文档签名算法
        host = "iat-api.xfyun.cn"
        api = "/v2/iat"
        now = int(time.time())
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(now))
        # 组装signature
        signature_origin = f"host: {host}\ndate: {date}\nGET {api} HTTP/1.1"
        signature_sha = base64.b64encode(
            hashlib.sha256(signature_origin.encode('utf-8')).digest()
        ).decode('utf-8')
        authorization_origin = (
            f'api_key="{self.api_key}",algorithm="hmac-sha256",headers="host date request-line",signature="{signature_sha}"'
        )
        # 组装最终URL
        params = {
            "authorization": base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8'),
            "date": date,
            "host": host,
        }
        url = self.ws_url + "?" + "&".join([f"{k}={requests.utils.quote(v)}" for k, v in params.items()])
        return url

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            code = data.get("code", -1)
            if code != 0:
                logger.error(f"ASR识别返回错误: code={code}, msg={data.get('message')}")
                self.finished.set()
                return
            result = data["data"]["result"]["ws"]
            text = ""
            for r in result:
                for w in r["cw"]:
                    text += w["w"]
            with self.result_lock:
                self.result += text
            # 若为最终结果（流结束）
            if data["data"]["status"] == 2:
                self.finished.set()
        except Exception as e:
            logger.error(f"ASR返回解析异常: {e}")
            self.finished.set()

    def _on_error(self, ws, error):
        logger.error(f"ASR websocket异常: {error}")
        self.finished.set()

    def _on_close(self, ws, *args):
        logger.info("ASR websocket连接关闭")
        self.finished.set()

    def _on_open(self, ws):
        # 本地直接录音保存为16k 16bit 单通道
        def send_audio():
            try:
                # 发首帧
                frame_size = 1280    # 40ms一帧，16k采样，单通道，16bit=2字节
                intervel = 0.04      # 发送间隔
                audio = self.audio_data
                idx = 0
                status = 0  # 0首帧，1中间帧，2尾帧
                total_len = len(audio)
                while idx < total_len:
                    chunk = audio[idx:idx+frame_size]
                    if idx == 0:
                        status = 0
                    elif idx+frame_size >= total_len:
                        status = 2
                    else:
                        status = 1
                    d = {
                        "common": {
                            "app_id": self.app_id
                        },
                        "business": {
                            "language": "zh_cn",
                            "domain": "iat",
                            "accent": "mandarin",
                            "vad_eos": 5000,
                            "dwa": "wpgs"
                        },
                        "data": {
                            "status": status,
                            "format": "audio/L16;rate=16000",
                            "encoding": "raw",
                            "audio": base64.b64encode(chunk).decode('utf-8')
                        }
                    }
                    ws.send(json.dumps(d))
                    idx += frame_size
                    time.sleep(intervel)
                # 最后一帧
                if status != 2:
                    d = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "encoding": "raw",
                            "audio": ""
                        }
                    }
                    ws.send(json.dumps(d))
            except Exception as e:
                logger.error(f"ASR音频分帧发送异常: {e}")
                self.finished.set()
        threading.Thread(target=send_audio).start()

    def recognize(self, audio, samplerate=16000):
        """
        :param audio: numpy数组或bytes(单声道16k)
        :param samplerate: 必须16k
        :return: 识别文本
        """
        # audio可为numpy或bytes
        if isinstance(audio, np.ndarray):
            audio = audio.astype(np.int16).tobytes()
        elif isinstance(audio, bytes):
            pass
        else:
            raise ValueError("audio只能为numpy数组或bytes")
        self.audio_data = audio
        self.result = ""
        self.finished.clear()
        url = self._assemble_url()

        ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        wst = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
        wst.daemon = True
        wst.start()
        # 阻塞直到全部结果收齐/异常
        self.finished.wait(timeout=30)
        return self.result.strip()
