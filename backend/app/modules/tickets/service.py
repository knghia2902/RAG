from typing import Optional
from app.modules.tickets.contracts import ValidationResult
from app.modules.tickets.validator import TicketSchemaValidator

MAX_TICKET_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


class TicketService:
    """Service handling ticket intake, upload processing, and validation."""

    def __init__(self, validator: Optional[TicketSchemaValidator] = None):
        self.validator = validator or TicketSchemaValidator()

    def process_uploaded_ticket_file(self, filename: str, content_bytes: bytes) -> ValidationResult:
        """Process and validate an uploaded ticket file (JSON or CSV).

        Args:
            filename: Original name of the uploaded file.
            content_bytes: Raw bytes of the uploaded file.

        Returns:
            ValidationResult with parsed tickets or detailed line errors.

        Raises:
            ValueError: If file size exceeds 5MB or format is not supported.
        """
        if len(content_bytes) > MAX_TICKET_FILE_SIZE_BYTES:
            raise ValueError(f"Dung lượng tệp vượt quá giới hạn cho phép (tối đa {MAX_TICKET_FILE_SIZE_BYTES // (1024 * 1024)}MB)")

        lower_name = filename.lower()
        if not (lower_name.endswith(".json") or lower_name.endswith(".csv")):
            raise ValueError("Định dạng tệp không được hỗ trợ. Vui lòng tải lên tệp .json hoặc .csv")

        try:
            # Handle utf-8-sig to automatically strip BOM if present
            decoded_text = content_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            raise ValueError(f"Tệp không thể giải mã theo chuẩn UTF-8: {e}")

        if lower_name.endswith(".json"):
            return self.validator.validate_json(decoded_text)
        else:
            return self.validator.validate_csv(decoded_text)
