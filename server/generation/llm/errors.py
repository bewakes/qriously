class LLMError(Exception):
    def __init__(self, code, message="", *, retryable=False):
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message or code)
