from uuid import UUID
from fastapi import APIRouter, Depends, Query
from app.database.session import get_db
from app.database import datasets
from app.api.dependencies import get_account
from app.api.users import mutation_manager
from app.api.schemas import DatasetDTO, DatasetPage, DatasetCreate, DatasetPatch

router = APIRouter(prefix="/api/v1", tags=["datasets"])


@router.get("/datasets", response_model=DatasetPage)
def list_datasets(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), account=Depends(get_account), db=Depends(get_db)):
    return datasets.list_metadata(db, account, page, page_size)


@router.get("/datasets/{dataset_id}", response_model=DatasetDTO)
def detail(dataset_id: UUID, account=Depends(get_account), db=Depends(get_db)):
    return datasets.detail_metadata(db, account, dataset_id)


@router.post("/admin/datasets", response_model=DatasetDTO, status_code=201)
def create(payload: DatasetCreate, account=Depends(mutation_manager), db=Depends(get_db)):
    return datasets.save_metadata(db, account, payload)


@router.patch("/admin/datasets/{dataset_id}", response_model=DatasetDTO)
def update(dataset_id: UUID, payload: DatasetPatch, account=Depends(mutation_manager), db=Depends(get_db)):
    return datasets.save_metadata(db, account, payload, dataset_id)
