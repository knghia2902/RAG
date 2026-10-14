import json
import logging
import re
from typing import Any, Optional

from app.llm.contracts import GenerationRequest, LLMProvider
from app.llm.secret_masking import mask_secrets
from app.modules.reports.contracts import ReportMetricsDTO, ReportNarrativeDTO

logger = logging.getLogger(__name__)


class ReportNarrativeSynthesizer:
    """
    Synthesizes executive summary, root cause narrative, and SOP recommendations.
    Employs mask_secrets before prompt egress and deterministic fallback when LLM is unavailable (SYS-05).
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self.llm_provider = llm_provider

    def synthesize_narrative(
        self,
        metrics: ReportMetricsDTO,
        period_description: str = "kỳ báo cáo",
        incident_samples: Optional[list[dict[str, Any]]] = None,
    ) -> ReportNarrativeDTO:
        if self.llm_provider is None:
            return self._build_deterministic_fallback(metrics)

        try:
            # Build structured prompt
            prompt_lines = [
                "Bạn là trợ lý chuyên gia phân tích vận hành hệ thống IT & Logistics.",
                f"Hãy phân tích số liệu vận hành và sự cố trong {period_description}:",
                f"- Tổng sự cố: {metrics.total_incidents}",
                f"- Tổng ticket IT: {metrics.total_tickets}",
                f"- Đã hoàn tất: {metrics.resolved_incidents}, Đang mở: {metrics.open_incidents}",
                f"- MTTR trung bình: {metrics.mttr_minutes if metrics.mttr_minutes is not None else 'Chưa có'}",
            ]

            if metrics.system_breakdown:
                top_sys = ", ".join(f"{s.system} ({s.percentage}%)" for s in metrics.system_breakdown[:3])
                prompt_lines.append(f"- Hệ thống chính bị ảnh hưởng: {top_sys}")

            if metrics.recurring_errors:
                rec_str = "; ".join(
                    f"{r.system}:{r.error_group} (lặp {r.occurrence_count} lần, ảnh hưởng {len(r.affected_orders)} đơn)"
                    for r in metrics.recurring_errors[:5]
                )
                prompt_lines.append(f"- Lỗi lặp lại nghiêm trọng: {rec_str}")

            if incident_samples:
                prompt_lines.append("\nMẫu sự cố tiêu biểu:")
                for s in incident_samples[:5]:
                    order_id = s.get("order_id", "N/A")
                    sys = s.get("system", "N/A")
                    eg = s.get("error_group", "N/A")
                    prompt_lines.append(f"  * Đơn {order_id} [{sys}]: {eg}")

            prompt_lines.append(
                "\nYêu cầu xuất định dạng JSON duy nhất với 4 trường:\n"
                "{\n"
                '  "executive_summary": "Tóm tắt điều hành bằng tiếng Việt",\n'
                '  "root_cause_analysis": "Phân tích nguyên nhân gốc rễ và hệ thống nghẽn",\n'
                '  "recommendations": ["Khuyến nghị 1 có nhắc đến SOP liên quan", "Khuyến nghị 2"],\n'
                '  "missing_data_warnings": ["Cảnh báo dữ liệu khuyết thiếu nếu có"]\n'
                "}"
            )

            raw_prompt = "\n".join(prompt_lines)
            safe_prompt = mask_secrets(raw_prompt)

            request = GenerationRequest(
                prompt=safe_prompt,
                max_tokens=800,
                temperature=0.2,
            )

            response = self.llm_provider.generate(request)
            raw_text = response.text if hasattr(response, "text") else str(response)

            match = re.search(r"\{[\s\S]*\}", raw_text)
            if not match:
                raise ValueError("LLM response does not contain valid JSON object")

            data = json.loads(match.group(0))
            return ReportNarrativeDTO(
                executive_summary=data.get("executive_summary", "").strip() or self._build_deterministic_fallback(metrics).executive_summary,
                root_cause_analysis=data.get("root_cause_analysis", "").strip() or self._build_deterministic_fallback(metrics).root_cause_analysis,
                recommendations=[str(r).strip() for r in data.get("recommendations", []) if str(r).strip()],
                missing_data_warnings=[str(w).strip() for w in data.get("missing_data_warnings", []) if str(w).strip()],
            )

        except Exception as e:
            logger.warning("Report narrative LLM synthesis failed, falling back to deterministic: %s", e)
            warning_msg = f"LLM gặp sự cố hoặc timeout ({type(e).__name__}); áp dụng nhận định quy tắc dự phòng theo SYS-05."
            return self._build_deterministic_fallback(metrics, warning=warning_msg)

    def _build_deterministic_fallback(
        self,
        metrics: ReportMetricsDTO,
        warning: Optional[str] = None,
    ) -> ReportNarrativeDTO:
        top_system_str = "Hệ thống chung"
        if metrics.system_breakdown:
            top_s = max(metrics.system_breakdown, key=lambda x: x.incident_count)
            top_system_str = f"{top_s.system} ({top_s.percentage}%)"

        exec_summary = (
            f"Trong kỳ báo cáo, hệ thống ghi nhận tổng cộng {metrics.total_incidents} sự cố "
            f"và {metrics.total_tickets} ticket IT. Số lượng sự cố đã hoàn tất xử lý là {metrics.resolved_incidents}, "
            f"số sự cố đang mở là {metrics.open_incidents}. Phân bổ hệ thống ghi nhận tải sự cố tập trung tại {top_system_str}."
        )

        if metrics.recurring_errors:
            rec_details = ", ".join(
                f"{r.system}:{r.error_group} ({r.occurrence_count} lần)"
                for r in metrics.recurring_errors[:3]
            )
            root_cause = (
                f"Nguyên nhân vận hành nổi cộm xuất phát từ các nhóm lỗi lặp lại: {rec_details}. "
                "Cần kiểm tra lại cấu hình kết nối, tải hệ thống mạng và tính toàn vẹn dữ liệu đơn hàng tương ứng."
            )
        else:
            root_cause = (
                "Các sự cố trong kỳ phân tán trên các dịch vụ thành phần, không ghi nhận mẫu lỗi lặp lại vượt ngưỡng cảnh báo."
            )

        recommendations: list[str] = []
        if metrics.recurring_errors:
            for r in metrics.recurring_errors[:3]:
                recommendations.append(
                    f"Rà soát và xử lý nhóm lỗi {r.system}: {r.error_group} (lặp {r.occurrence_count} lần) theo quy trình chuẩn SOP liên quan."
                )

        if metrics.open_incidents > 0:
            recommendations.append(
                f"Tập trung nhân lực kỹ thuật đóng dứt điểm {metrics.open_incidents} sự cố đang mở để ổn định chỉ số MTTR."
            )

        if not recommendations:
            recommendations.append("Tiếp tục theo dõi và kiểm soát định kỳ các cổng kết nối WMS, TMS và API Gateway.")

        warnings: list[str] = []
        if warning:
            warnings.append(warning)
        if metrics.open_incidents > 0:
            warnings.append(
                f"Ghi nhận {metrics.open_incidents} sự cố đang mở chưa có thời gian đóng; chỉ số MTTR chỉ tính trên các sự cố đã hoàn tất."
            )

        return ReportNarrativeDTO(
            executive_summary=exec_summary,
            root_cause_analysis=root_cause,
            recommendations=recommendations,
            missing_data_warnings=warnings,
        )
