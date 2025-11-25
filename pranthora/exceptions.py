class PranthoraError(Exception):
    pass

class APIError(PranthoraError):
    def __init__(self, message, status_code=None, body=None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

class AuthenticationError(APIError):
    pass

class PermissionError(APIError):
    pass

class NotFoundError(APIError):
    pass

class RateLimitError(APIError):
    pass

class APIConnectionError(PranthoraError):
    pass
