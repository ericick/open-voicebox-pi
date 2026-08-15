from openai import OpenAI
from utils.logger import logger

REPLY_FORMAT_HINT = "回答要简短，最多3句话；不要使用任何星号、破折号、列表符号或换行；不要反问用户。"

class DeepseekAdapter:
    def __init__(self, api_key, base_url="https://api.deepseek.com", model="deepseek-chat", temperature=0.7, max_tokens=2048, system_prompt="", web_search=False):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        if system_prompt and REPLY_FORMAT_HINT not in system_prompt:
            self.system_prompt = system_prompt + " " + REPLY_FORMAT_HINT
        self.web_search = web_search

    def _build_messages(self, context):
        # 保证 system prompt 始终在最前面
        messages = context[-20:]  # 取最近20条
        if self.system_prompt:
            # 判断是否已经有system prompt，没有则插入
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            # 如果已经有system，建议替换成新的system
            elif messages[0].get("role") == "system":
                messages[0]["content"] = self.system_prompt
        return messages

    def chat(self, context):
        messages = self._build_messages(context)

        # 联网搜索模式：优先走 /responses + web_search，失败自动降级为普通对话
        if self.web_search:
            reply = self._chat_with_search(messages)
            if reply is not None:
                return reply
            logger.warning("DeepSeek联网搜索不可用，降级为普通对话")

        try:
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

    def _chat_with_search(self, messages):
        """调用 DeepSeek 官方网页搜索接口（/responses + web_search），失败返回 None。"""
        try:
            response = self.client.responses.create(
                model=self.model,
                input=messages,
                tools=[{"type": "web_search", "web_search": {"search_context_size": "medium"}}],
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            text = getattr(response, "output_text", None)
            if text and text.strip():
                logger.info(f"DeepSeek联网回复: {text.strip()}")
                return text.strip()
        except Exception as e:
            logger.error(f"DeepSeek联网接口异常: {e}")
        return None
