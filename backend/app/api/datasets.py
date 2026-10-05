from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from app.database.session import get_db
from app.auth.policy import dataset_query
from app.api.dependencies import get_account
from app.api.schemas import DatasetDTO, DatasetPage

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.get("", response_model=DatasetPage)
def list_datasets(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), account=Depends(get_account), db=Depends(get_db)):
    query = dataset_query(account)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by("name").offset((page - 1) * page_size).limit(page_size)).all()
    return DatasetPage(items=[DatasetDTO.model_validate(row) for row in rows], total=total, page=page, page_size=page_size)
