import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.database.session import SessionLocal
from app.database.models import (
    Account,
    Dataset,
    DatasetGrant,
    Source,
    SourceVersion,
    ImportJob,
    ParseRun,
    CanonicalRecord,
    EmbeddingRecord,
)
from app.providers import get_embedding_provider

def seed_demo_rag():
    with SessionLocal() as db:
        # 1. Tìm hoặc tạo Dataset Vận hành Logistics
        dataset = db.scalar(select(Dataset).where(Dataset.name == "Vận hành Logistics & Kho bãi"))
        if not dataset:
            dataset = Dataset(
                name="Vận hành Logistics & Kho bãi",
                description="Dữ liệu mẫu đơn hàng và quy trình vận hành kho WMS để kiểm thử RAG"
            )
            db.add(dataset)
            db.flush()
            print(f"Created dataset: {dataset.name} ({dataset.id})")
        else:
            print(f"Found existing dataset: {dataset.name} ({dataset.id})")

        # Gán quyền cho admin và guest
        for u in ("admin", "guest"):
            acc = db.scalar(select(Account).where(Account.username == u))
            if acc:
                grant = db.scalar(select(DatasetGrant).where(DatasetGrant.account_id == acc.id, DatasetGrant.dataset_id == dataset.id))
                if not grant:
                    db.add(DatasetGrant(account_id=acc.id, dataset_id=dataset.id))
                    print(f"Granted dataset to {u}")

        # 2. Tìm hoặc tạo Source
        source = db.scalar(select(Source).where(Source.dataset_id == dataset.id, Source.logical_filename == "don_hang_wms.txt"))
        if not source:
            source = Source(
                dataset_id=dataset.id,
                logical_filename="don_hang_wms.txt",
                profile_id="operational",
            )
            db.add(source)
            db.flush()

        # 3. SourceVersion
        version = db.scalar(select(SourceVersion).where(SourceVersion.source_id == source.id, SourceVersion.version_number == 1))
        if not version:
            version = SourceVersion(
                source_id=source.id,
                version_number=1,
                content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                storage_key="sample/don_hang_wms.txt",
                size_bytes=1024,
                mime_type="text/plain",
            )
            db.add(version)
            db.flush()
            source.active_version_id = version.id
            db.flush()

        # 4. ImportJob & ParseRun
        job = db.scalar(select(ImportJob).where(ImportJob.source_version_id == version.id))
        if not job:
            job = ImportJob(
                source_version_id=version.id,
                state="ready",
                attempt_count=1,
            )
            db.add(job)
            db.flush()

        run = db.scalar(select(ParseRun).where(ParseRun.source_version_id == version.id))
        if not run:
            run = ParseRun(
                source_version_id=version.id,
                job_id=job.id,
                parser_name="text_chunker",
                parser_version="1.0",
                status="published",
            )
            db.add(run)
            db.flush()

        # 5. CanonicalRecords & Embeddings
        chunks = [
            (
                "Đơn hàng DH001: Kiện hàng 25kg vận chuyển từ Kho Sóng Thần đến Trung tâm Phân phối Bắc Ninh, trạng thái Đang giao hàng ngày 12/10/2026. Người nhận: Nguyễn Văn An, SĐT: 0901234567.",
                {"page": 1, "line": 1, "paragraph": 1}
            ),
            (
                "Đơn hàng DH010: Kiện hàng 10kg vận chuyển từ Kho Tân Bình đến Chi nhánh Cần Thơ, trạng thái Đã hoàn tất giao ngày 10/10/2026. Người nhận: Lê Thị Bình, ghi chú: Đã ký nhận.",
                {"page": 1, "line": 15, "paragraph": 2}
            ),
            (
                "Đơn hàng DH0011: Kiện hàng linh kiện vi mạch điện tử 5kg, trạng thái Tạm giữ hải quan chờ kiểm hóa bổ sung chứng từ CO/CQ.",
                {"page": 1, "line": 28, "paragraph": 3}
            ),
            (
                "Quy trình xử lý sự cố SOP-LOG-01: Khi phát hiện đơn hàng bị chậm trễ trên 48 giờ hoặc có mã lỗi ERR-502, kỹ thuật viên phải kiểm tra mã đơn hàng (ví dụ DH001) trên WMS và lập biên bản sự cố vận tải.",
                {"page": 2, "line": 1, "paragraph": 4}
            )
        ]

        embed_provider = get_embedding_provider()
        model_name = getattr(embed_provider, "model", "fake-embedding-small")
        dim = getattr(embed_provider, "dimension", 1536)
        idx_version = getattr(embed_provider, "_index_version", uuid.uuid4())

        existing_records = db.scalars(select(CanonicalRecord).where(CanonicalRecord.source_version_id == version.id)).all()
        if not existing_records:
            for pos, (text, loc) in enumerate(chunks, start=1):
                rec = CanonicalRecord(
                    parse_run_id=run.id,
                    source_version_id=version.id,
                    dataset_id=dataset.id,
                    position=pos,
                    locator_data=loc,
                    content_text=text,
                    record_metadata={"source": "don_hang_wms.txt"}
                )
                db.add(rec)
                db.flush()

                vector = embed_provider.embed_texts([text])[0]
                emb = EmbeddingRecord(
                    canonical_record_id=rec.id,
                    dataset_id=dataset.id,
                    source_version_id=version.id,
                    model_name=model_name,
                    dimension=dim,
                    index_version=idx_version,
                    embedding=vector
                )
                db.add(emb)
                print(f"Inserted record #{pos}: {text[:40]}...")

        db.commit()
        print("SEED_DEMO_RAG_SUCCESS")

if __name__ == "__main__":
    seed_demo_rag()
