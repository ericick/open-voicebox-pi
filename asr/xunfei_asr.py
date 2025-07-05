import time
import json
import base64
import hashlib
import hmac
import threading
import websocket
import ssl
import numpy as np
from utils.logger import logger
from urllib.parse import quote_plus

class XunfeiASR:
    def __init__(self, app_id, api_key, api_secret, hotwords=""):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.hotwords = hotwords
        self.ws_url = "wss://iat-api.xfyun.cn/v2/iat"
        self.result = ""
        self.result_lock = threading.Lock()
        self.finished = threading.Event()

    def _assemble_url(self):
        host = "iat-api.xfyun.cn"
        api = "/v2/iat"
        url = self.ws_url

        # 1. 生成RFC1123格式时间戳
        now = time.time()
        date = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(now))
        logger.debug(f"ASR鉴权用date: {date}")

        # 2. 组装签名原始字符串
        signature_origin = f"host: {host}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += f"GET {api} HTTP/1.1"
        logger.debug(f"ASR签名原始串: {repr(signature_origin)}")

        # 3. HMAC-SHA256签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')
        logger.debug(f"ASR签名base64: {signature}")

        # 4. 组装authorization_origin字符串
        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        logger.debug(f"ASR authorization_origin: {authorization_origin}")
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        logger.debug(f"ASR authorization (base64): {authorization}")

        # 6. 拼接url参数
        params = {
            "authorization": authorization,
            "date": date,
            "host": host,
        }
        url = url + '?' + '&'.join([f"{k}={quote_plus(v)}" for k, v in params.items()])
        logger.info(f"ASR WS 连接URL: {url}")
        return url

    def _on_message(self, ws, message):
        logger.debug(f"ASR收到消息: {message[:500]}")
        try:
            data = json.loads(message)
            code = data.get("code", -1)
            if code != 0:
                logger.error(f"ASR识别返回错误: code={code}, msg={data.get('message')}")
                self.finished.set()
                return
            # 只处理最后一帧
            if data["data"]["status"] == 2:
                ws_list = data["data"]["result"]["ws"]
                text = ""
                for r in ws_list:
                    for w in r["cw"]:
                        text += w["w"]
                with self.result_lock:
                    self.result = text  # 覆盖，保证是最后完整的一句
                logger.info(f"ASR识别完成，最终结果: {self.result.strip()}")
                self.finished.set()
            # 其他帧不处理
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
        def send_audio():
            try:
                frame_size = 1280    # 40ms一帧，16k采样，单通道，16bit=2字节
                intervel = 0.04      # 发送间隔
                audio = self.audio_data
                idx = 0
                status = 0
                total_len = len(audio)
                logger.info(f"ASR总音频字节: {total_len}, 开始分帧发送")
                while idx < total_len:
                    chunk = audio[idx:idx+frame_size]
                    if idx == 0:
                        status = 0
                    elif idx+frame_size >= total_len:
                        status = 2
                    else:
                        status = 1
                    logger.debug(f"发送到ASR，第{idx//frame_size}帧，状态: {status}, chunk字节: {len(chunk)}")
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
                if status != 2:
                    logger.debug("补发最后一帧（status=2，audio空）")
                    d = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "encoding": "raw",
                            "audio": ""
                        }
                    }
                    ws.send(json.dumps(d))
                logger.info("ASR所有音频已发送")
            except Exception as e:
                logger.error(f"ASR音频分帧发送异常: {e}")
                self.finished.set()
        threading.Thread(target=send_audio).start()

    def recognize(self, audio, samplerate=16000):
        """
        一次性音频识别：audio为完整录音（numpy数组或bytes），自动分帧发送
        """
        logger.info(f"调用ASR一次性识别，audio类型:{type(audio)}, 长度:{len(audio) if isinstance(audio, bytes) else audio.size}")
        if isinstance(audio, np.ndarray):
            audio = audio.astype(np.int16).tobytes()
        elif isinstance(audio, bytes):
            pass
        else:
            logger.error("audio只能为numpy数组或bytes")
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
        self.finished.wait(timeout=30)
        if self.result.strip():
            logger.info(f"ASR最终识别文本: {self.result.strip()}")
        else:
            logger.error("ASR未识别到有效文本")
        return self.result.strip()

    def recognize_stream(self, audio_generator):
        """
        边录音边识别（流式）：audio_generator为yield音频块(bytes)的生成器
        """
        self.result = ""
        self.finished.clear()
        url = self._assemble_url()

        def send_audio(ws):
            status = 0  # 0首帧 1中间帧 2尾帧
            try:
                logger.info("ASR流式识别：开始分块发送")
                for idx, audio_chunk in enumerate(audio_generator):
                    if idx == 0:
                        status = 0
                    else:
                        status = 1
                    logger.debug(f"流式ASR，第{idx}帧，状态: {status}, chunk字节: {len(audio_chunk)}")
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
                            "audio": base64.b64encode(audio_chunk).decode('utf-8')
                        }
                    }
                    ws.send(json.dumps(d))
                    time.sleep(0.04)
                # 发送尾帧
                logger.debug("流式ASR，发送尾帧（status=2）")
                d = {
                    "data": {
                        "status": 2,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": ""
                    }
                }
                ws.send(json.dumps(d))
                logger.info("流式ASR所有音频已发送")
            except Exception as e:
                logger.error(f"ASR流式音频发送异常: {e}")
                self.finished.set()

        def on_open(ws):
            threading.Thread(target=send_audio, args=(ws,)).start()

        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        wst = threading.Thread(target=ws.run_forever, kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}})
        wst.daemon = True
        wst.start()
        self.finished.wait(timeout=30)
        if self.result.strip():
            logger.info(f"ASR流式最终识别文本: {self.result.strip()}")
        else:
            logger.error("ASR流式未识别到有效文本")
        return self.result.strip()
