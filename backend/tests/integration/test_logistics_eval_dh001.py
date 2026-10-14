from uuid import uuid4
import pytest
from app.auth.passwords import hash_password
from app.database.models import (
    Account,
    CanonicalRecord,
    Dataset,
    DatasetGrant,
    EmbeddingRecord,
    ImportJob,
    ParseRun,
    Source,
    SourceVersion,
)
from app.providers.fake import FakeEmbeddingAdapter
from tests.conftest import HEADERS, PASSWORD


@pytest.fixture
def seeded_logistics_eval_environment(db):
    """Seed comprehensive multi-system logistics data for EVAL-01."""
    # 1. Tech user & Dataset
    tech = Account(
        username=f"tech_eval_{uuid4().hex[:6]}",
        display_name="Kỹ thuật viên Vận hành Sóng Thần",
        role="technician",
        password_hash=hash_password(PASSWORD),
    )
    dataset = Dataset(name=f"Dataset-Logistics-EVAL-{uuid4().hex[:8]}")
    db.add_all([tech, dataset])
    db.flush()

    grant = DatasetGrant(account_id=tech.id, dataset_id=dataset.id)
    db.add(grant)
    db.flush()

    embedding_adapter = FakeEmbeddingAdapter()

    def add_source_with_records(filename: str, profile: str, records: list[str]):
        src = Source(dataset_id=dataset.id, logical_filename=filename, profile_id=profile)
        db.add(src)
        db.flush()

        ver = SourceVersion(
            source_id=src.id,
            version_number=1,
            content_hash=uuid4().hex,
            storage_key=f"storage_{filename}",
            size_bytes=len("".join(records).encode("utf-8")),
            mime_type="text/plain",
        )
        db.add(ver)
        db.flush()
        src.active_version_id = ver.id

        job = ImportJob(source_version_id=ver.id, state="ready")
        db.add(job)
        db.flush()

        run = ParseRun(
            source_version_id=ver.id,
            job_id=job.id,
            parser_name="text_log" if profile == "text_log" else "document",
            parser_version="1.0",
            status="published",
        )
        db.add(run)
        db.flush()

        canon_records = []
        for idx, text in enumerate(records, start=1):
            cr = CanonicalRecord(
                parse_run_id=run.id,
                source_version_id=ver.id,
                dataset_id=dataset.id,
                position=idx,
                locator_data={"line_start": idx, "line_end": idx},
                content_text=text,
            )
            db.add(cr)
            db.flush()
            canon_records.append(cr)

            # Generate embedding record
            vec = list(embedding_adapter.embed((text,))[0])
            emb = EmbeddingRecord(
                canonical_record_id=cr.id,
                dataset_id=dataset.id,
                source_version_id=ver.id,
                model_name=embedding_adapter.model,
                dimension=embedding_adapter.dimension,
                index_version=embedding_adapter.index.index_version,
                embedding=vec,
            )
            db.add(emb)

        return src, ver, canon_records

    # 1. WMS Log
    add_source_with_records(
        filename="wms_songthan_orders.log",
        profile="text_log",
        records=[
            "2026-10-14 08:10:00 [INFO] Order DH001 created at Kho Sóng Thần, items: 25kg, customer: CUST-881",
            "2026-10-14 08:15:00 [INFO] Order DH001 packing completed, status: PACKED, ready for dispatch at Gate 4",
            "2026-10-14 09:00:00 [INFO] Order DH010 packing completed, status: PACKED at Gate 1",
            "2026-10-14 09:10:00 [INFO] Order DH0011 created at Kho Sóng Thần, items: 10kg",
        ],
    )

    # 2. API Gateway Log
    add_source_with_records(
        filename="api_gateway_access.log",
        profile="text_log",
        records=[
            "2026-10-14 08:15:02 [INFO] POST /api/v1/sync/order_id=DH001 from WMS to TMS Dispatch Service",
            "2026-10-14 08:15:05 [ERROR] Upstream TMS timeout after 3000ms: POST /tms/v1/shipments for DH001 -> HTTP 504 Gateway Timeout",
            "2026-10-14 09:00:03 [INFO] POST /tms/v1/shipments for DH010 -> HTTP 200 OK",
            "2026-10-14 09:10:05 [INFO] POST /tms/v1/shipments for DH0011 -> HTTP 200 OK",
        ],
    )

    # 3. TMS Log (DH001 is missing here!)
    add_source_with_records(
        filename="tms_dispatch.log",
        profile="text_log",
        records=[
            "2026-10-14 09:00:10 [INFO] Order DH010 received and assigned to Truck 29C-12345",
            "2026-10-14 09:10:15 [INFO] Order DH0011 received and assigned to Truck 51D-99999",
        ],
    )

    # 4. SOP Document
    add_source_with_records(
        filename="SOP-LOG-01_Xu_Ly_Loi_Dong_Bo_WMS_TMS.txt",
        profile="sop",
        records=[
            "QUY TRÌNH CHUẨN SOP-LOG-01: Xử lý sự cố mất đồng bộ dữ liệu đơn hàng giữa hệ thống Kho (WMS) và Điều phối vận tải (TMS).",
            "Mục 2.1: Khi phát hiện lỗi HTTP 504 Gateway Timeout trên API Gateway, kỹ thuật viên kiểm tra endpoint /healthz của dịch vụ TMS.",
            "Mục 2.3: Thực hiện gọi API tái kích hoạt đồng bộ POST /api/v1/orders/{order_id}/sync-retry từ WMS sang TMS.",
        ],
    )

    db.commit()
    return tech, dataset


def test_eval_dh001_incident_analysis_e2e(client, db, seeded_logistics_eval_environment):
    """Acceptance test EVAL-01: End-to-end incident analysis for order DH001 against ground truth metrics."""
    tech, _ = seeded_logistics_eval_environment

    # 1. Tech login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    assert login_res.status_code == 200
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    # 2. Trigger analysis for DH001
    analyze_res = client.post(
        "/api/v1/incidents/analyze",
        json={"order_id": "DH001", "description": "Đơn DH001 đóng gói nhưng không thấy tài xế đến nhận"},
        headers=h,
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()

    # Metric 1: Order ID Disambiguation
    assert data["order_id"] == "DH001"
    for ev in data["timeline"]:
        assert "DH001" in ev["raw_snippet"]
        assert "DH010" not in ev["raw_snippet"]
        assert "DH0011" not in ev["raw_snippet"]

    # Metric 2: Classification Accuracy (INC-03)
    assert "Mất đồng bộ" in data["classification"]["error_group"] or "timeout" in data["classification"]["error_group"].lower()
    assert data["classification"]["primary_system"] == "API_GATEWAY"
    assert data["classification"]["suggested_priority"] == "P1"
    assert data["classification"]["confidence"] >= 0.85

    # Metric 3: First Sync Failure Point Isolation (INC-01, D-04)
    failure_events = [ev for ev in data["timeline"] if ev["is_failure_point"] is True]
    assert len(failure_events) == 1
    failure = failure_events[0]
    assert failure["system"] == "API_GATEWAY"
    assert "504" in failure["raw_snippet"]

    # Metric 4: Root Cause Hypotheses vs Confirmed Cause (INC-05)
    confirmed_hypotheses = [h for h in data["hypotheses"] if h["is_confirmed"] is True]
    assert len(confirmed_hypotheses) >= 1
    assert any("504" in h["hypothesis"] or "timeout" in h["hypothesis"].lower() for h in confirmed_hypotheses)
    assert failure["citation_id"] in confirmed_hypotheses[0]["supporting_evidence_citations"]

    # Metric 5: RAG-05 Missing Data Warning
    assert len(data["missing_information"]) >= 1
    assert any("TMS" in item for item in data["missing_information"])

    # Metric 6: SOP Procedure Attribution (INC-04)
    assert len(data["recommended_actions"]) >= 2
    assert all("SOP-LOG-01" in act["sop_reference"] for act in data["recommended_actions"])


def test_eval_dh010_healthy_order_comparison(client, db, seeded_logistics_eval_environment):
    """Acceptance test: Order DH010 is processed successfully without false positive failure point."""
    tech, _ = seeded_logistics_eval_environment

    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": tech.username, "password": PASSWORD},
        headers=HEADERS,
    )
    h = {**HEADERS, "X-CSRF-Token": login_res.json()["csrf_token"]}

    analyze_res = client.post(
        "/api/v1/incidents/analyze",
        json={"order_id": "DH010"},
        headers=h,
    )
    assert analyze_res.status_code == 200
    data = analyze_res.json()

    # Timeline has events across WMS, API_GATEWAY and TMS
    assert data["order_id"] == "DH010"
    assert len(data["timeline"]) == 3
    # No false failure point
    assert all(ev["is_failure_point"] is False for ev in data["timeline"])
    assert data["classification"]["suggested_priority"] in ("P3", "P4")
