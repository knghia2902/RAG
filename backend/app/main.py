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
    except Exception:
        response = JSONResponse(status_code=503, content={"detail": "Dịch vụ tạm thời không khả dụng"})
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.get("/health/live")
def live():
    return {"status": "live"}

@app.get("/health/ready")
def ready():
    from sqlalchemy import text
    from app.database.session import SessionLocal
    with SessionLocal() as db:
        if db.execute(text("SELECT version_num FROM alembic_version")).scalar_one() != "0001_access_control":
            from fastapi import HTTPException
            raise HTTPException(503, "Migration required")
    return {"status": "ready"}

from app.api.auth import router as auth_router
from app.api.datasets import router as datasets_router
app.include_router(auth_router)
app.include_router(datasets_router)
from app.config import get_settings
if get_settings().test_mode:
    from tests.support import router as test_router
    app.include_router(test_router)
