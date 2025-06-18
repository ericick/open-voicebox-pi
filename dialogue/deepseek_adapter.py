from openai import OpenAI
from utils.logger import logger

class DeepseekAdapter:
    def __init__(self, api_key, base_url="https://api.deepseek.com", model="deepseek-chat", temperature=0.7, max_tokens=2048):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, context):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context[-20:],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False
            )
            logger.info(f"DeepSeek回复: {response.choices[0].message.content}")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"DeepSeek接口异常: {e}")
            return "对不起，我暂时无法回答你的问题。"
