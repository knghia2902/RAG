import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_account
from app.auth.policy import verify_dataset_access
from app.database.models import Account, ExtractedImage, SourceVersion
from app.database.session import get_db

router = APIRouter(
    prefix="/api/v1/datasets/{dataset_id}/sources/{source_id}/images",
    tags=["images"],
)


@router.get("/{image_id}")
async def get_extracted_image(
    dataset_id: uuid.UUID,
    source_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """
    Phục vụ hình ảnh tài liệu đã trích xuất với kiểm tra quyền truy cập (ACL)
    và Live Scope Recheck (D-08, T-07-02, T-07-03).
    """
    # 1. Kiểm tra xác thực quyền dataset (Live Scope Recheck)
    verify_dataset_access(account, dataset_id, db)

    # 2. Truy vấn bản ghi ExtractedImage khớp dataset_id, source_id, image_id
    stmt = (
        select(ExtractedImage)
        .join(SourceVersion, ExtractedImage.source_version_id == SourceVersion.id)
        .where(
            ExtractedImage.id == image_id,
            ExtractedImage.dataset_id == dataset_id,
            SourceVersion.source_id == source_id,
        )
    )
    image_record = db.scalar(stmt)
    if image_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hình ảnh.",
        )

    # 3. Kiểm tra file vật lý trên đĩa lưu trữ
    if not os.path.exists(image_record.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tệp hình ảnh không tồn tại trên hệ thống lưu trữ.",
        )

    # 4. Trả về FileResponse kèm Cache-Control private và nosniff
    return FileResponse(
        path=image_record.storage_path,
        media_type=image_record.mime_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )
