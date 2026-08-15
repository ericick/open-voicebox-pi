"""对话路由：普通对话走 DeepSeek，复杂任务走 Codex，Codex 失败自动降级。"""

from utils.logger import logger


class DialogueRouter:
    def __init__(self, default_adapter, codex_adapter,
                 enabled=False, triggers=None, min_length=40):
        self.default_adapter = default_adapter
        self.codex_adapter = codex_adapter
        self.enabled = enabled
        self.triggers = triggers or []
        self.min_length = min_length

    def chat(self, context):
        """与各适配器同签名；内部决定走 DeepSeek 还是 Codex。"""
        if not context or context[-1].get("role") != "user":
            return self.default_adapter.chat(context)
        user_text = context[-1].get("content", "")
        if self.enabled and self._should_route(user_text):
            logger.info("命中复杂任务路由，尝试调用Codex")
            reply = self.codex_adapter.chat(context)
            if reply:
                return reply
            logger.warning("Codex未返回有效结果，降级到DeepSeek")
        return self.default_adapter.chat(context)

    def _should_route(self, user_text):
        if len(user_text) >= self.min_length:
            return True
        return any(t in user_text for t in self.triggers)
