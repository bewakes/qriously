class ContentBlocked(Exception):
    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)
