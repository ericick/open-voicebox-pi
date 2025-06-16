class EndwordDetector:
    def __init__(self, keywords):
        self.keywords = keywords

    def is_end(self, text):
        for word in self.keywords:
            if word in text:
                return True
        return False
