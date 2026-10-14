import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure app package is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select
from app.auth.passwords import hash_password
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    DatasetGrant,
    ImportJob,
    IncidentAnalysis,
    ParseRun,
    Report,
    Source,
    SourceVersion,
)
from app.database.session import SessionLocal
from app.modules.log_analysis.service import IncidentAnalysisService
from app.modules.reports.contracts import PeriodTypeEnum, ReportFilterDTO
from app.modules.reports.service import ReportService
from app.rag.parsers.text_log import TextLogParser
from app.rag.contracts import SourceLocator

SAMPLE_FILES = [
    ("api_gateway_access.log", "text_log"),
    ("wms_songthan_orders.log", "text_log"),
    ("tms_dispatch.log", "text_log"),
    ("SOP-LOG-01_Xu_Ly_Loi_Dong_Bo_WMS_TMS.txt", "text_log"),
    ("sample_tickets.csv", "text_log"),
]


def resolve_sample_dir() -> Path:
    # 1. Inside backend folder
    p0 = Path(__file__).resolve().parent.parent / "data" / "sample" / "logistics_incidents"
    if p0.exists():
        return p0
    # 2. Host project root
    base = Path(__file__).resolve().parent.parent.parent
    p1 = base / "data" / "sample" / "logistics_incidents"
    if p1.exists():
        return p1
    p2 = Path("/app/data/sample/logistics_incidents")
    if p2.exists():
        return p2
    p3 = Path("data/sample/logistics_incidents").resolve()
    if p3.exists():
        return p3
    return p0


def run_walkthrough(dry_run: bool = False):
    print("=" * 75)
    print("  MODULAR RAG IT & LOGISTICS — ONE-CLICK DEMO WALKTHROUGH")
    print("=" * 75)

    sample_dir = resolve_sample_dir()
    print(f"[*] Thư mục dữ liệu mẫu: {sample_dir}")

    # Check existence of sample files
    missing_files = []
    for fname, _ in SAMPLE_FILES:
        fpath = sample_dir / fname
        if not fpath.exists():
            missing_files.append(fname)

    if missing_files:
        print(f"[!] CẢNH BÁO: Không tìm thấy một số tệp mẫu: {missing_files}")
    else:
        print("[OK] Đã kiểm tra 5/5 tệp dữ liệu mẫu chuẩn.")

    if dry_run:
        print("\n[DRY RUN] Đang kiểm tra kết nối CSDL...")
        with SessionLocal() as db:
            user_count = db.scalar(select(Account).limit(1))
            print(f"[OK] Kết nối CSDL thành công. Sẵn sàng khởi tạo.")
        print("[DRY RUN] Kiểm tra hoàn tất thành công (không ghi dữ liệu).")
        return

    with SessionLocal() as db:
        # Step 1: Bootstrap accounts
        print("\n[*] Bước 1: Khởi tạo tài khoản Quản trị viên và Kỹ thuật viên...")
        admin = db.scalar(select(Account).where(Account.username == "admin"))
        if not admin:
            admin = Account(
                username="admin",
                display_name="Quản trị viên Hệ thống",
                role="admin",
                password_hash=hash_password("Admin@123456"),
            )
            db.add(admin)
            db.flush()
            print("    [+] Đã tạo tài khoản Admin: admin / Admin@123456")
        else:
            print("    [=] Tài khoản Admin đã tồn tại.")

        tech = db.scalar(select(Account).where(Account.username == "tech"))
        if not tech:
            tech = Account(
                username="tech",
                display_name="Kỹ thuật viên Vận hành",
                role="technician",
                password_hash=hash_password("Tech@123456"),
            )
            db.add(tech)
            db.flush()
            print("    [+] Đã tạo tài khoản Kỹ thuật viên: tech / Tech@123456")
        else:
            print("    [=] Tài khoản Kỹ thuật viên đã tồn tại.")

        # Step 2: Create dataset
        print("\n[*] Bước 2: Thiết lập Dataset mẫu logistics...")
        dataset_name = "[Demo] Logistics Operations"
        dataset = db.scalar(select(Dataset).where(Dataset.name == dataset_name))
        if not dataset:
            dataset = Dataset(
                name=dataset_name,
                description="Bộ dữ liệu tích hợp sự cố WMS, TMS, API Gateway và tài liệu SOP vận hành kho.",
            )
            db.add(dataset)
            db.flush()
            print(f"    [+] Đã tạo Dataset: {dataset_name} ({dataset.id})")
        else:
            print(f"    [=] Dataset đã tồn tại: {dataset_name}")

        # Grant access
        for acc in (admin, tech):
            grant = db.scalar(
                select(DatasetGrant).where(
                    DatasetGrant.account_id == acc.id, DatasetGrant.dataset_id == dataset.id
                )
            )
            if not grant:
                db.add(DatasetGrant(account_id=acc.id, dataset_id=dataset.id))
                print(f"    [+] Cấp quyền Dataset cho: {acc.username}")

        db.commit()

        # Step 3: Seed sample files into Source & CanonicalRecord
        print("\n[*] Bước 3: Nạp tệp log, SOP và ticket mẫu vào hệ thống RAG...")
        parser = TextLogParser()
        total_records = 0

        for fname, profile_id in SAMPLE_FILES:
            fpath = sample_dir / fname
            if not fpath.exists():
                continue

            content = fpath.read_bytes()

            source = db.scalar(
                select(Source).where(Source.dataset_id == dataset.id, Source.logical_filename == fname)
            )
            if not source:
                source = Source(
                    dataset_id=dataset.id,
                    logical_filename=fname,
                    profile_id=profile_id,
                )
                db.add(source)
                db.flush()

                version = SourceVersion(
                    source_id=source.id,
                    version_number=1,
                    content_hash=f"hash_{uuid4().hex[:12]}",
                    storage_key=f"sample/{fname}",
                    size_bytes=len(content),
                    mime_type="text/plain",
                )
                db.add(version)
                db.flush()
                source.active_version_id = version.id

                job = ImportJob(source_version_id=version.id, state="ready")
                db.add(job)
                db.flush()

                run = ParseRun(
                    source_version_id=version.id,
                    job_id=job.id,
                    parser_name=profile_id,
                    parser_version="1.0",
                    status="published",
                )
                db.add(run)
                db.flush()

                # Parse and add canonical records
                parse_result = parser.parse_bytes(
                    content=content,
                    locator_base=SourceLocator(source_id=source.id, source_version=1),
                    dataset_id=dataset.id,
                )
                for rec in parse_result.records:
                    # Extract order ID if present in line
                    order_match = re_order = None
                    import re
                    m = re.search(r"\b(DH\d{3,4})\b", rec.content_text)
                    meta = dict(rec.record_metadata)
                    if m:
                        meta["order_id"] = m.group(1)

                    db.add(
                        CanonicalRecord(
                            parse_run_id=run.id,
                            source_version_id=version.id,
                            dataset_id=dataset.id,
                            position=rec.position,
                            locator_data=rec.locator.model_dump(mode="json"),
                            content_text=rec.content_text,
                            record_metadata=meta,
                        )
                    )
                    total_records += 1

                print(f"    [+] Nạp thành công tệp: {fname} ({len(parse_result.records)} bản ghi)")
            else:
                print(f"    [=] Tệp đã nạp trước đó: {fname}")

        db.commit()

        # Step 4: Run Incident Analysis for DH001
        print("\n[*] Bước 4: Thực hiện phân tích sự cố mẫu cho đơn hàng DH001...")
        service = IncidentAnalysisService(db=db)
        existing_analysis = db.scalar(
            select(IncidentAnalysis).where(IncidentAnalysis.order_id == "DH001")
        )
        if not existing_analysis:
            analysis_rec, result = service.analyze_order(
                account=tech,
                order_id="DH001",
                description="Đơn hàng DH001 bị nghẽn đồng bộ giữa WMS và TMS, khách hàng khiếu nại trễ đơn.",
            )
            print(f"    [+] Đã sinh phân tích sự cố: ID {analysis_rec.id}")
            print(f"        - Nhóm lỗi: {analysis_rec.classification_json.get('error_group')}")
            print(f"        - Hệ thống chính: {analysis_rec.classification_json.get('primary_system')}")
            print(f"        - Số sự kiện liên kết: {len(analysis_rec.timeline_json)}")
        else:
            print(f"    [=] Hồ sơ sự cố DH001 đã có sẵn: ID {existing_analysis.id}")

        # Step 5: Generate Weekly Incident Report
        print("\n[*] Bước 5: Sinh báo cáo sự cố định kỳ tuần & xuất bản PDF...")
        existing_report = db.scalar(
            select(Report).where(Report.period_type == "weekly").order_by(Report.created_at.desc())
        )
        if not existing_report:
            filter_dto = ReportFilterDTO(
                period_type=PeriodTypeEnum.WEEKLY,
                dataset_ids=[dataset.id],
            )
            report = ReportService.generate_report(
                db=db,
                account_id=tech.id,
                filter_dto=filter_dto,
                allowed_dataset_ids={dataset.id},
            )
            db.commit()
            print(f"    [+] Đã sinh báo cáo tuần: ID {report.id} - '{report.title}'")
            print(f"        - Tổng sự cố trong kỳ: {report.metrics_json.get('total_incidents')}")
            print(f"        - Tổng tickets: {report.metrics_json.get('total_tickets')}")
        else:
            print(f"    [=] Báo cáo tuần đã có sẵn: ID {existing_report.id}")

    # Step 6: Summary and instructions
    print("\n" + "=" * 75)
    print("  KHỞI TẠO HOÀN TẤT! SẴN SÀNG TRẢI NGHIỆM HỆ THỐNG WEB RAG")
    print("=" * 75)
    print("1. Địa chỉ Web UI:       http://localhost:3000")
    print("2. Tài khoản Kỹ thuật:   Username: tech   | Mật khẩu: Tech@123456")
    print("3. Tài khoản Quản trị:   Username: admin  | Mật khẩu: Admin@123456")
    print("-" * 75)
    print("Hướng dẫn trải nghiệm 3 bước nhanh:")
    print("  • Bước 1: Đăng nhập tại http://localhost:3000/login bằng tài khoản 'tech'.")
    print("  • Bước 2: Mở tab 'Sự cố' (http://localhost:3000/incidents) xem phân tích đơn hàng DH001.")
    print("  • Bước 3: Mở tab 'Báo cáo' (http://localhost:3000/reports) xem số liệu tuần và tải file PDF.")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="One-Click Demo Walkthrough Setup Script")
    parser.add_argument("--dry-run", action="store_true", help="Kiểm tra kết nối và tệp mẫu mà không ghi vào CSDL")
    args = parser.parse_args()

    run_walkthrough(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
