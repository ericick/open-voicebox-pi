import re

class EndwordDetector:
    def __init__(self, keywords=None):
        # 可配置化，支持拼音/正则/多种表达
        self.keywords = keywords or ["再见", "拜拜", "下次再说", "回头聊", "关闭"]
        # 可扩展正则表达式，覆盖变体
        self.patterns = [re.compile(k) for k in self.keywords]

    def is_end(self, text):
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False
