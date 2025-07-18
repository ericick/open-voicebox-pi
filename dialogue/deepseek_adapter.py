from openai import OpenAI 
from utils.logger import logger

class DeepseekAdapter:
    def __init__(self, api_key, base_url="https://api.deepseek.com", model="deepseek-chat", temperature=0.7, max_tokens=2048, system_prompt=""):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

    def chat(self, context):
        try:
            # 保证 system prompt 始终在最前面
            messages = context[-20:]  # 取最近20条
            if self.system_prompt:
                # 判断是否已经有system prompt，没有则插入
                if not messages or messages[0].get("role") != "system":
                    messages = [{"role": "system", "content": self.system_prompt}] + messages
                # 如果已经有system，建议替换成新的system
                elif messages[0].get("role") == "system":
                    messages[0]["content"] = self.system_prompt

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            logger.info(f"DeepSeek回复: {response.choices[0].message.content}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek接口异常: {e}")
            return "对不起，我暂时无法回答你的问题。"
