from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def validation_error(request: Request, exc: RequestValidationError):
    # Pydantic errors include input values; never reflect passwords or tokens.
    return JSONResponse(status_code=422, content={"detail": "Dữ liệu không hợp lệ"}, headers={"Cache-Control": "no-store"})
