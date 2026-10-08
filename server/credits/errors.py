class InsufficientCredits(Exception):
    def __init__(self, required: int, balance: int) -> None:
        self.required = required
        self.balance = balance
        super().__init__(f"required {required}, available {balance}")
