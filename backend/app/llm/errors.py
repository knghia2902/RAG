"""LLM and Provider exception taxonomy and user-facing error response formatting (SYS-05)."""


class LLMBaseError(Exception):
    """Base exception for LLM operations."""
    def __init__(self, message: str = "", retryable: bool = False):
        super().__init__(message)
        self.message = message
        self.retryable = retryable


class LLMTimeoutError(LLMBaseError):
    """Lỗi timeout khi gọi LLM Provider."""
    def __init__(self, message: str = "LLM provider timed out", retryable: bool = True):
        super().__init__(message, retryable=retryable)


class LLMQuotaExceededError(LLMBaseError):
    """Lỗi vượt hạn mức quota hoặc rate limit."""
    def __init__(self, message: str = "LLM quota/rate limit exceeded", retryable: bool = True):
        super().__init__(message, retryable=retryable)


class LLMAuthenticationError(LLMBaseError):
    """Lỗi xác thực API key nhà cung cấp."""
    def __init__(self, message: str = "Invalid LLM provider credentials", retryable: bool = False):
        super().__init__(message, retryable=retryable)


class LLMServiceError(LLMBaseError):
    """Lỗi nội bộ từ dịch vụ LLM Provider."""
    def __init__(self, message: str = "LLM provider internal service error", retryable: bool = True):
        super().__init__(message, retryable=retryable)


def format_llm_error_response(error: Exception) -> dict:
    """Định dạng thông điệp lỗi tiếng Việt thân thiện theo Copywriting Contract (03-UI-SPEC.md)."""
    if isinstance(error, LLMTimeoutError):
        category = "timeout"
        retryable = True
        msg = "Thời gian phản hồi từ nhà cung cấp AI đã hết. Vui lòng thử lại câu hỏi."
    elif isinstance(error, LLMQuotaExceededError):
        category = "quota_exceeded"
        retryable = True
        msg = "Hệ thống AI đang tạm thời vượt quá giới hạn lượt gọi. Vui lòng thử lại sau giây lát."
    elif isinstance(error, LLMAuthenticationError):
        category = "authentication"
        retryable = False
        msg = "Cấu hình khóa dịch vụ AI không hợp lệ. Vui lòng liên hệ Quản trị viên để kiểm tra cấu hình."
    else:
        category = "service_error"
        retryable = getattr(error, "retryable", False)
        msg = "Không thể hoàn thành truy xuất do lỗi kết nối hoặc vượt quá giới hạn. Kiểm tra kết nối mạng và thử gửi lại câu hỏi."

    return {
        "error": True,
        "category": category,
        "detail": msg,
        "retryable": retryable,
    }
