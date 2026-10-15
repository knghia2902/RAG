from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.errors import validation_error
app = FastAPI(title="Logistics RAG", version="0.1.0")
app.add_exception_handler(RequestValidationError, validation_error)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        response = JSONResponse(status_code=503, content={"detail": "Dịch vụ tạm thời không khả dụng"})
    if "Cache-Control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
app.include_router(auth_router)
app.include_router(datasets_router)
from app.api import sources
app.include_router(sources.router)
from app.api.users import router as users_router
app.include_router(users_router)
from app.api.health import router as health_router
from app.api.status import router as status_router
from app.api import config
from app.api import chat
from app.api import incidents
from app.api import reports
from app.api import images
app.include_router(health_router)
app.include_router(status_router)
app.include_router(config.router)
app.include_router(chat.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(images.router)

from app.config import get_settings
if get_settings().test_mode:
    from tests.support import router as test_router
    app.include_router(test_router)

