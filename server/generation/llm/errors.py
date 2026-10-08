class LLMError(Exception):
    def __init__(
        self, code: str, message: str = "", *, retryable: bool = False
    ) -> None:
        self.code = code
        self.message = message
        self.retryable = retryable
        super().__init__(message or code)
