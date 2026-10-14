from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from app.database.session import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database_ready: bool


def database_ready() -> bool:
    try:
        with SessionLocal() as db:
            return db.execute(text("SELECT version_num FROM alembic_version")).scalar_one() in (
                "0001_access_control",
                "0002_source_lifecycle",
                "0003_pgvector_and_chat",
                "0004_incident_analysis",
            )
    except Exception:
        # Never expose driver messages, connection strings or credentials.
        return False


@router.get("/live")
def live():
    return {"status": "live"}


@router.get("/ready")
def ready():
    if not database_ready():
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@router.get("", response_model=HealthStatus)
def health():
    value = database_ready()
    return JSONResponse(status_code=200 if value else 503, content={"database_ready": value})
