"""Codex 无头调用适配器（Codex 壳 + DeepSeek 脑子）。

与 DeepseekAdapter 提供相同的 chat(context) 接口；
任何失败都返回 None，由上层路由自动降级回 DeepSeek，
保证音箱始终有回答。
"""

import os
import shutil
import subprocess

from utils.logger import logger

# codex exec 会把最后一条消息写入这个文件，然后由我们读回
_OUTPUT_FILE = "/tmp/voicebox_codex_last_msg.txt"

# 需要从子进程环境中清除的代理变量（沿用 run.sh 的直连策略）
_PROXY_KEYS = ("http_proxy", "https_proxy", "all_proxy",
               "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")


class CodexAdapter:
    def __init__(self, model="deepseek-v4-flash", provider="deepseek",
                 system_prompt="", timeout_s=120, working_dir=None):
        self.model = model
        self.provider = provider
        self.system_prompt = system_prompt
        self.timeout_s = timeout_s
        self.working_dir = working_dir or os.getcwd()
        self.codex_bin = shutil.which("codex") or "codex"
        if self.codex_bin == "codex" and not shutil.which("codex"):
            logger.warning("未找到 codex 命令，复杂任务路由将自动降级为 DeepSeek")

    def chat(self, context):
        """与 DeepseekAdapter.chat 同签名；失败返回 None。"""
        prompt = self._build_prompt(context)
        cmd = [
            self.codex_bin, "exec",
            "-s", "read-only",
            "-C", self.working_dir,
            "-c", f'model_provider="{self.provider}"',
            "-m", self.model,
            "-o", _OUTPUT_FILE,
            "--", prompt,
        ]
        env = os.environ.copy()
        for key in _PROXY_KEYS:
            env.pop(key, None)
        try:
            logger.info(f"Codex调用开始: model={self.model} timeout={self.timeout_s}s")
            proc = subprocess.run(cmd, env=env, capture_output=True,
                                  text=True, timeout=self.timeout_s)
            if proc.returncode != 0:
                logger.error(f"Codex退出码异常: {proc.returncode}，{proc.stderr[-300:]}")
                return None
            try:
                with open(_OUTPUT_FILE, "r", encoding="utf-8") as f:
                    text = f.read().strip()
            except OSError:
                logger.error("读取Codex输出文件失败")
                return None
            if not text:
                logger.warning("Codex输出为空，降级处理")
                return None
            logger.info(f"Codex回复: {text[:150]}")
            return text
        except subprocess.TimeoutExpired:
            logger.error(f"Codex调用超时({self.timeout_s}秒)，降级处理")
            return None
        except FileNotFoundError:
            logger.error("找不到codex命令，降级处理")
            return None
        except Exception as e:
            logger.error(f"Codex调用异常: {e}，降级处理")
            return None

    def _build_prompt(self, context):
        lines = []
        if self.system_prompt:
            lines.append(f"你是语音助手，请始终记住以下设定：{self.system_prompt}")
        lines.append("以下是最近的对话历史：")
        for msg in context[-10:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            lines.append(f"{role}: {msg.get('content', '')}")
        lines.append("")
        lines.append(
            "请直接回答用户最新提出的问题。要求：回答简短，最多3句话；"
            "只输出要朗读出来的内容本身，不要任何markdown符号、列表、括号语气词或反问；"
            "需要实时信息（如天气、新闻、股票、时间）时可以使用你的工具获取；不要修改任何文件。"
        )
        return "\n".join(lines)
