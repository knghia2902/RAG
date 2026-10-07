import secrets
from urllib.parse import urlparse
from fastapi import HTTPException, Request
from app.config import get_settings
from app.auth.sessions import digest


def validate_request(request: Request):
    origin = get_settings().app_origin
    # Next rewrites change Host to the exact internal destination. Origin stays
    # browser supplied; do not accept arbitrary X-Forwarded-Host/IP headers.
    internal_host = "api-test:8000" if get_settings().test_mode else "backend:8000"
    if request.headers.get("origin") != origin or request.headers.get("host") not in {urlparse(origin).netloc, internal_host}:
        raise HTTPException(403, "Yêu cầu không hợp lệ")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in ("application/json", "multipart/form-data"):
        raise HTTPException(415, "Yêu cầu JSON")
    if request.headers.get("x-requested-with") != "RAG-Web":
        raise HTTPException(403, "Yêu cầu không hợp lệ")


def validate_csrf(request, row):
    token = request.headers.get("x-csrf-token", "")
    if not token or len(token) > 128 or not secrets.compare_digest(digest(token), row.csrf_digest):
        raise HTTPException(403, "Yêu cầu không hợp lệ")
