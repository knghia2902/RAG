import argparse
import json
import os
import sys
from pathlib import Path
import statistics
import time
from datetime import datetime, timezone
from uuid import uuid4

# Ensure app package is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.reports.contracts import (
    PeriodTypeEnum,
    PriorityDistributionDTO,
    RecurringErrorItemDTO,
    ReportDetailDTO,
    ReportMetricsDTO,
    ReportNarrativeDTO,
    SystemDistributionDTO,
)
from app.modules.reports.pdf_generator import ReportPDFGenerator
from app.modules.log_analysis.contracts import CorrelatedOrderLogs, TimelineEventDTO
from app.modules.log_analysis.correlator import CrossSystemLogCorrelator
from app.modules.log_analysis.reasoner import IncidentReasoner
from app.modules.tickets.contracts import SystemEnum
from app.providers.fake import FakeLLMAdapter
from app.rag.contracts import SourceLocator
from app.rag.parsers.text_log import TextLogParser


def create_sample_report_dto() -> ReportDetailDTO:
    now = datetime.now(timezone.utc)
    metrics = ReportMetricsDTO(
        total_incidents=15,
        total_tickets=12,
        resolved_incidents=10,
        open_incidents=5,
        mttr_minutes=24.5,
        system_breakdown=[
            SystemDistributionDTO(system="API_GATEWAY", incident_count=8, ticket_count=6, percentage=53.3),
            SystemDistributionDTO(system="WMS", incident_count=4, ticket_count=4, percentage=26.7),
            SystemDistributionDTO(system="TMS", incident_count=3, ticket_count=2, percentage=20.0),
        ],
        priority_breakdown=[
            PriorityDistributionDTO(priority="P1", count=4, percentage=26.7),
            PriorityDistributionDTO(priority="P2", count=6, percentage=40.0),
            PriorityDistributionDTO(priority="P3", count=5, percentage=33.3),
        ],
        error_group_breakdown={"504_GATEWAY_TIMEOUT": 6, "OUT_OF_STOCK": 4, "DRIVER_UNREACHABLE": 3, "OTHER": 2},
        recurring_errors=[
            RecurringErrorItemDTO(
                system="API_GATEWAY",
                error_group="504_GATEWAY_TIMEOUT",
                occurrence_count=6,
                percentage=40.0,
                affected_orders=["DH001", "DH002", "DH004", "DH007"],
                sample_message="504 Gateway Timeout connecting to TMS Dispatch service",
            )
        ],
    )
    narrative = ReportNarrativeDTO(
        executive_summary="Báo cáo tuần ghi nhận 15 sự cố vận hành, trong đó lỗi nghiêm trọng nhất là mất đồng bộ WMS-TMS do timeout tại API Gateway.",
        root_cause_analysis="Hạ tầng mạng cụm TMS gặp hiện tượng nghẽn hàng đợi lúc cao điểm dẫn đến các request điều phối bị quá 30 giây.",
        recommendations=[
            "Tăng timeout kết nối giữa API Gateway và TMS từ 30s lên 45s.",
            "Bổ sung cơ chế circuit breaker và retry tự động với exponential backoff.",
            "Kiểm tra lại capacity của cụm server TMS Dispatch.",
        ],
        missing_data_warnings=["Thiếu log đối soát từ hệ thống ERP đối tác trong ngày 12/10."],
    )
    return ReportDetailDTO(
        id=uuid4(),
        title="Báo cáo sự cố tuần - Logistics Operations (Benchmark)",
        period_type=PeriodTypeEnum.WEEKLY,
        start_time=now,
        end_time=now,
        timezone="Asia/Ho_Chi_Minh",
        dataset_ids=[str(uuid4())],
        metrics=metrics,
        narrative=narrative,
        provenance_sources=[{"source_id": str(uuid4()), "filename": "wms_songthan_orders.log", "version": 1}],
        created_at=now,
    )


def compute_quantiles(data: list[float]) -> tuple[float, float, float, float]:
    """Return min, max, p50, and p95 in milliseconds."""
    if not data:
        return 0.0, 0.0, 0.0, 0.0
    ms_data = [d * 1000 for d in data]
    min_val = round(min(ms_data), 2)
    max_val = round(max(ms_data), 2)
    p50_val = round(statistics.median(ms_data), 2)

    if len(ms_data) >= 20:
        p95_val = round(statistics.quantiles(ms_data, n=100)[94], 2)
    else:
        # For small sample sizes, take the highest or interpolated near-max
        sorted_data = sorted(ms_data)
        idx = int(0.95 * len(sorted_data))
        p95_val = round(sorted_data[min(idx, len(sorted_data) - 1)], 2)

    return min_val, max_val, p50_val, p95_val


def benchmark_ingestion(iterations: int, base_dir: Path) -> list[float]:
    sample_log = base_dir / "data" / "sample" / "logistics_incidents" / "wms_songthan_orders.log"
    if not sample_log.exists():
        sample_log = base_dir.parent / "data" / "sample" / "logistics_incidents" / "wms_songthan_orders.log"

    content = sample_log.read_bytes() if sample_log.exists() else b"[2026-10-14 10:00:00] [WMS] Test log line\n" * 100
    parser = TextLogParser()
    loc = SourceLocator(source_id=uuid4(), source_version=1)
    ds_id = uuid4()

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = parser.parse_bytes(content, locator_base=loc, dataset_id=ds_id)
        times.append(time.perf_counter() - t0)
    return times


def benchmark_correlation(iterations: int) -> list[float]:
    correlator = CrossSystemLogCorrelator()
    dummy_records = [
        {"text": f"[2026-10-14 10:0{i % 10}:00] [API_GATEWAY] [INFO] Request for DH001 processed", "line": i}
        for i in range(50)
    ]
    dummy_records.append({
        "text": "[2026-10-14 10:09:50] [API_GATEWAY] [ERROR] Order DH001 failed with 504 Gateway Timeout",
        "line": 51,
    })

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = correlator.correlate_order(order_id="DH001", raw_records=dummy_records)
        times.append(time.perf_counter() - t0)
    return times


def benchmark_generation(iterations: int, live: bool = False) -> list[float]:
    provider = FakeLLMAdapter()
    reasoner = IncidentReasoner(llm_provider=provider)

    correlator = CrossSystemLogCorrelator()
    sample_records = [
        {"text": "[2026-10-14 10:00:00] [WMS] [INFO] Packaging order DH001", "line": 1},
        {"text": "[2026-10-14 10:00:15] [API_GATEWAY] [ERROR] Order DH001 timeout 504", "line": 2},
    ]
    correlated = correlator.correlate_order(order_id="DH001", raw_records=sample_records)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = reasoner.analyze_incident(order_id="DH001", correlated_logs=correlated, sop_evidences=[])
        times.append(time.perf_counter() - t0)
    return times


def benchmark_pdf_export(iterations: int) -> list[float]:
    pdf_gen = ReportPDFGenerator()
    report_dto = create_sample_report_dto()

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = pdf_gen.generate_pdf(report_dto)
        times.append(time.perf_counter() - t0)
    return times


def main():
    parser = argparse.ArgumentParser(description="Multi-Stage Latency Benchmarking Harness")
    parser.add_argument("--iterations", type=int, default=5, help="Number of benchmark iterations per stage")
    parser.add_argument("--live", action="store_true", help="Run with live OpenAI API provider if available")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Path to write JSON results")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent.parent

    print("=" * 75)
    print(" MODULAR RAG FOR IT & LOGISTICS - LATENCY BENCHMARKING HARNESS")
    print("=" * 75)
    print(f"Iterations: {args.iterations} | Live API: {args.live}")
    print("-" * 75)

    stages = [
        ("Ingestion (Parse & Chunk)", lambda: benchmark_ingestion(args.iterations, project_root)),
        ("Retrieval & Correlation", lambda: benchmark_correlation(args.iterations)),
        ("Generation & Reasoning", lambda: benchmark_generation(args.iterations, live=args.live)),
        ("WeasyPrint PDF Render", lambda: benchmark_pdf_export(args.iterations)),
    ]

    results = {}

    print(f"{'Giai đoạn / Thành phần':<30} | {'Mẫu':<5} | {'Min (ms)':<9} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'Max (ms)':<9}")
    print("-" * 75)

    for stage_name, bench_fn in stages:
        raw_times = bench_fn()
        min_v, max_v, p50_v, p95_v = compute_quantiles(raw_times)
        results[stage_name] = {
            "samples": len(raw_times),
            "min_ms": min_v,
            "p50_ms": p50_v,
            "p95_ms": p95_v,
            "max_ms": max_v,
        }
        print(f"{stage_name:<30} | {len(raw_times):<5} | {min_v:<9} | {p50_v:<9} | {p95_v:<9} | {max_v:<9}")

    print("-" * 75)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Báo cáo chi tiết đã được xuất ra: {output_path.resolve()}\n")


if __name__ == "__main__":
    main()
