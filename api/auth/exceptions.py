class InvalidEmail(BaseException):
    def __init__(self, invalid_email: str):
        self.invalid_email = invalid_email

    @property
    def detail(self):
        return f"email '{self.invalid_email}' is invalid"