import csv
import io
import json
from typing import Any
from pydantic import ValidationError
from app.modules.tickets.contracts import (
    TicketImportRow,
    ValidationResult,
    LineValidationError,
)

REQUIRED_CSV_COLUMNS = {"ticket_id", "order_id", "timestamp", "system", "severity", "description"}


class TicketSchemaValidator:
    """Strict schema validator for Ticket import files (JSON and CSV)."""

    def validate_json(self, raw_text: str) -> ValidationResult:
        """Validate JSON formatted ticket records."""
        if not raw_text or not raw_text.strip():
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[LineValidationError(line=1, message="Tệp JSON rỗng hoặc không có dữ liệu")],
            )

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[LineValidationError(line=1, message=f"Định dạng JSON không hợp lệ: {e}")],
            )

        if not isinstance(data, list):
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[
                    LineValidationError(
                        line=1,
                        message="Tệp JSON phải chứa một mảng danh sách các bản ghi ticket (list of objects)",
                    )
                ],
            )

        tickets: list[TicketImportRow] = []
        errors: list[LineValidationError] = []

        for index, item in enumerate(data):
            line_no = index + 1
            if not isinstance(item, dict):
                errors.append(
                    LineValidationError(
                        line=line_no,
                        message="Mỗi bản ghi ticket trong JSON phải là một đối tượng (object)",
                    )
                )
                continue

            try:
                ticket = TicketImportRow.model_validate(item)
                tickets.append(ticket)
            except ValidationError as ve:
                for err in ve.errors():
                    field_name = ".".join(str(loc) for loc in err["loc"])
                    msg = err["msg"]
                    if "Field required" in msg:
                        friendly_msg = f"Thiếu trường bắt buộc '{field_name}'"
                    elif "String should match pattern" in msg:
                        friendly_msg = f"Trường '{field_name}' chứa ký tự không hợp lệ, chỉ chấp nhận chữ cái, số, gạch dưới và gạch ngang"
                    elif "Input should be" in msg:
                        friendly_msg = f"Giá trị trường '{field_name}' không hợp lệ: {msg}"
                    else:
                        friendly_msg = f"Trường '{field_name}' không hợp lệ: {msg}"

                    errors.append(
                        LineValidationError(
                            line=line_no,
                            field=field_name,
                            message=friendly_msg,
                            invalid_value=str(item.get(field_name, "")),
                        )
                    )

        if errors:
            return ValidationResult(
                is_valid=False,
                total_rows=len(data),
                tickets=[],
                errors=errors,
            )

        return ValidationResult(
            is_valid=True,
            total_rows=len(tickets),
            tickets=tickets,
            errors=[],
        )

    def validate_csv(self, raw_text: str) -> ValidationResult:
        """Validate CSV formatted ticket records."""
        if not raw_text or not raw_text.strip():
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[LineValidationError(line=1, message="Tệp CSV rỗng hoặc không có dữ liệu")],
            )

        stream = io.StringIO(raw_text.strip())
        reader = csv.DictReader(stream)

        if not reader.fieldnames:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[LineValidationError(line=1, message="Tệp CSV không có tiêu đề cột (header)")],
            )

        fieldnames = {col.strip() for col in reader.fieldnames if col}
        missing_columns = REQUIRED_CSV_COLUMNS - fieldnames
        if missing_columns:
            return ValidationResult(
                is_valid=False,
                total_rows=0,
                tickets=[],
                errors=[
                    LineValidationError(
                        line=1,
                        message=f"Tệp CSV thiếu các cột bắt buộc: {', '.join(sorted(missing_columns))}",
                    )
                ],
            )

        tickets: list[TicketImportRow] = []
        errors: list[LineValidationError] = []
        total_rows = 0

        for line_no, raw_row in enumerate(reader, start=2):
            total_rows += 1
            cleaned_row: dict[str, Any] = {}
            for k, v in raw_row.items():
                if k is not None:
                    key = k.strip()
                    val = v.strip() if isinstance(v, str) else v
                    # Sanitize CSV formula injection prefixes
                    if isinstance(val, str) and val.startswith(("=", "+", "-", "@")):
                        val = val.lstrip("=+-@").strip()
                    cleaned_row[key] = val

            try:
                ticket = TicketImportRow.model_validate(cleaned_row)
                tickets.append(ticket)
            except ValidationError as ve:
                for err in ve.errors():
                    field_name = ".".join(str(loc) for loc in err["loc"])
                    msg = err["msg"]
                    if "Field required" in msg:
                        friendly_msg = f"Thiếu trường bắt buộc '{field_name}'"
                    elif "String should match pattern" in msg:
                        friendly_msg = f"Trường '{field_name}' chứa ký tự không hợp lệ"
                    else:
                        friendly_msg = f"Trường '{field_name}' không hợp lệ: {msg}"

                    errors.append(
                        LineValidationError(
                            line=line_no,
                            field=field_name,
                            message=friendly_msg,
                            invalid_value=str(cleaned_row.get(field_name, "")),
                        )
                    )

        if errors:
            return ValidationResult(
                is_valid=False,
                total_rows=total_rows,
                tickets=[],
                errors=errors,
            )

        return ValidationResult(
            is_valid=True,
            total_rows=total_rows,
            tickets=tickets,
            errors=[],
        )
