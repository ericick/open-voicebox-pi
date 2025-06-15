import requests
from utils.logger import logger

class DeepseekAdapter:
    def __init__(self, api_key, api_url="https://api.deepseek.com/v1/chat/completions"):
        self.api_key = api_key
        self.api_url = api_url

    def chat(self, user_text, context=None):
        # context可选，便于实现多轮对话
        payload = {
            "model": "deepseek-chat",  # 替换为实际模型名
            "messages": [{"role": "user", "content": user_text}]
        }
        if context:
            payload["messages"] = context + [{"role": "user", "content": user_text}]
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            logger.info(f"Deepseek回复: {reply}")
            return reply.strip()
        except Exception as e:
            logger.error(f"Deepseek接口调用失败: {e}")
            return "对不起，我暂时无法回答你的问题。"
