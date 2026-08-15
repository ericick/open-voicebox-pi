class EndwordDetector:
    def __init__(self, keywords):
        self.keywords = keywords

    def is_end(self, text):
        lowered = text.lower()
        for word in self.keywords:
            if word.lower() in lowered:
                return True
        return False
