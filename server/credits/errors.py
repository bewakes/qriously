class InsufficientCredits(Exception):
    def __init__(self, required, balance):
        self.required = required
        self.balance = balance
        super().__init__(f"required {required}, available {balance}")
