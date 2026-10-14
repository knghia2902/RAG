from datetime import datetime, timezone
import uuid
import pytest

from app.modules.reports.contracts import (
    PeriodTypeEnum,
    PriorityDistributionDTO,
    RecurringErrorItemDTO,
    ReportDetailDTO,
    ReportMetricsDTO,
    ReportNarrativeDTO,
    SystemDistributionDTO,
)
from app.modules.reports.pdf_generator import ReportPDFGenerator, _blocked_url_fetcher


def _build_sample_report(title: str = "Báo cáo sự cố tháng 10") -> ReportDetailDTO:
    now = datetime(2026, 10, 14, 8, 30, 0, tzinfo=timezone.utc)
    metrics = ReportMetricsDTO(
        total_incidents=15,
        total_tickets=10,
        resolved_incidents=12,
        open_incidents=3,
        mttr_minutes=35.5,
        system_breakdown=[
            SystemDistributionDTO(system="API_GATEWAY", incident_count=8, ticket_count=5, percentage=53.3),
            SystemDistributionDTO(system="WMS", incident_count=5, ticket_count=3, percentage=33.3),
            SystemDistributionDTO(system="TMS", incident_count=2, ticket_count=2, percentage=13.3),
        ],
        priority_breakdown=[
            PriorityDistributionDTO(priority="P1", count=4, percentage=26.7),
            PriorityDistributionDTO(priority="P2", count=6, percentage=40.0),
            PriorityDistributionDTO(priority="P3", count=5, percentage=33.3),
        ],
        error_group_breakdown={
            "504_GATEWAY_TIMEOUT": 6,
            "INVENTORY_MISMATCH": 4,
            "LOCATION_NOT_FOUND": 3,
        },
        recurring_errors=[
            RecurringErrorItemDTO(
                system="API_GATEWAY",
                error_group="504_GATEWAY_TIMEOUT",
                occurrence_count=6,
                percentage=40.0,
                affected_orders=["DH001", "DH002", "DH008", "DH010"],
                sample_message="API_GATEWAY: 504_GATEWAY_TIMEOUT",
            )
        ],
    )

    narrative = ReportNarrativeDTO(
        executive_summary="Trong kỳ ghi nhận sự cố nghẽn mạng API Gateway ảnh hưởng tới luồng xử lý đơn hàng nhanh.",
        root_cause_analysis="Timeout kết nối giữa API Gateway và cơ sở dữ liệu WMS vào khung giờ cao điểm.",
        recommendations=[
            "Tăng cấu hình connection pool cho API Gateway theo tài liệu SOP-IT-04.",
            "Khởi động lại dịch vụ điều hướng tin nhắn khi độ trễ vượt ngưỡng 500ms.",
        ],
        missing_data_warnings=["Một số bản ghi log TMS thiếu thông tin mã xe trung chuyển."],
    )

    return ReportDetailDTO(
        id=uuid.uuid4(),
        title=title,
        period_type=PeriodTypeEnum.MONTHLY,
        start_time=datetime(2026, 9, 30, 17, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 10, 31, 16, 59, 59, 999999, tzinfo=timezone.utc),
        timezone="Asia/Ho_Chi_Minh",
        dataset_ids=[str(uuid.uuid4())],
        metrics=metrics,
        narrative=narrative,
        provenance_sources=[
            {
                "source_id": str(uuid.uuid4()),
                "version_number": 1,
                "filename": "wms_production_logs.log",
                "dataset_id": str(uuid.uuid4()),
            }
        ],
        created_at=now,
    )


def test_render_html_escaping():
    generator = ReportPDFGenerator()
    xss_payload = "<script>alert('xss')</script>"
    report = _build_sample_report(title=xss_payload)

    html = generator.render_html(report)
    assert "<script>" not in html
    assert "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in html or "&lt;script&gt;" in html


def test_ssrf_blocked_url_fetcher():
    with pytest.raises(PermissionError):
        _blocked_url_fetcher("http://169.254.169.254/latest/meta-data")


def test_generate_pdf_magic_bytes_and_vietnamese():
    pytest.importorskip("weasyprint")
    generator = ReportPDFGenerator()
    vn_title = "Báo cáo sự cố hệ thống kho Sóng Thần & điều phối giao vận"
    report = _build_sample_report(title=vn_title)

    pdf_bytes = generator.generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-1.")
