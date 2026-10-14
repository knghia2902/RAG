from pathlib import Path
from typing import Any, Optional
import zoneinfo
import jinja2

from app.modules.reports.contracts import ReportDetailDTO

VN_TZ = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")


def _blocked_url_fetcher(url: str, timeout: int = 5, ssl_context: Any = None) -> dict[str, Any]:
    """
    Prevents SSRF and unauthorized network access during PDF rendering.
    All images, fonts, and stylesheets must be embedded or local.
    """
    raise PermissionError(f"External network requests are blocked in PDF generation: {url}")


class ReportPDFGenerator:
    def __init__(self, template_dir: Optional[Path] = None) -> None:
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / "templates"
        self.template_dir = template_dir
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )

    def render_html(self, report: ReportDetailDTO) -> str:
        template = self.jinja_env.get_template("incident_report.html")

        # Format datetimes in Asia/Ho_Chi_Minh timezone
        s_local = report.start_time.astimezone(VN_TZ) if report.start_time.tzinfo else report.start_time.replace(tzinfo=VN_TZ)
        e_local = report.end_time.astimezone(VN_TZ) if report.end_time.tzinfo else report.end_time.replace(tzinfo=VN_TZ)
        c_local = report.created_at.astimezone(VN_TZ) if report.created_at.tzinfo else report.created_at.replace(tzinfo=VN_TZ)

        return template.render(
            report=report,
            formatted_start_time=s_local.strftime("%d/%m/%Y %H:%M:%S"),
            formatted_end_time=e_local.strftime("%d/%m/%Y %H:%M:%S"),
            formatted_created_at=c_local.strftime("%d/%m/%Y %H:%M:%S"),
        )

    def generate_pdf(self, report: ReportDetailDTO) -> bytes:
        import weasyprint

        html_content = self.render_html(report)
        html_doc = weasyprint.HTML(
            string=html_content,
            base_url=str(self.template_dir),
            url_fetcher=_blocked_url_fetcher,
        )
        return html_doc.write_pdf()
