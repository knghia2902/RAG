from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from app.api.dependencies import get_account
from app.api.health import database_ready
from app.auth.policy import current_account, require_admin
from app.config import get_settings
from app.database.session import get_db

router = APIRouter(prefix="/api/v1/status", tags=["configuration"])


class ConfigurationStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database_ready: bool
    provider_configured: bool


@router.get("", response_model=ConfigurationStatus)
def status(account=Depends(get_account), db=Depends(get_db)):
    require_admin(current_account(db, account))
    value = ConfigurationStatus(database_ready=database_ready(),
                                provider_configured=bool(get_settings().openai_api_key.get_secret_value().strip()))
    require_admin(current_account(db, account))
    return value
