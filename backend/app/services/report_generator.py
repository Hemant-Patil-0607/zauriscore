import json
import io
import boto3
from datetime import datetime, timezone
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.core.config import settings


DECISION_COLORS = {
    "GO": "#16a34a",
    "REVIEW": "#d97706",
    "NO-GO": "#dc2626",
}

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#d97706",
    "low": "#2563eb",
    "informational": "#6b7280",
}


class ReportGenerator:

    def __init__(self):
        self._s3 = None

    @property
    def s3(self):
        if self._s3 is None:
            self._s3 = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
                region_name=settings.s3_region,
            )
        return self._s3

    def generate_all(self, scan_id: str, scan_data: Dict) -> Dict[str, str]:
        """Generates JSON, Markdown, and PDF reports and uploads to S3."""
        json_url = self._generate_json(scan_id, scan_data)
        md_url = self._generate_markdown(scan_id, scan_data)
        pdf_url = self._generate_pdf(scan_id, scan_data)

        return {
            "json_url": json_url,
            "md_url": md_url,
            "pdf_url": pdf_url,
        }

    def _upload(self, key: str, content: bytes, content_type: str) -> str:
        self._ensure_bucket()
        self.s3.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        if settings.s3_endpoint_url:
            return f"{settings.s3_endpoint_url}/{settings.s3_bucket_name}/{key}"
        return f"https://{settings.s3_bucket_name}.s3.{settings.s3_region}.amazonaws.com/{key}"

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=settings.s3_bucket_name)
        except Exception:
            self.s3.create_bucket(Bucket=settings.s3_bucket_name)

    def _generate_json(self, scan_id: str, data: Dict) -> str:
        content = json.dumps(data, indent=2, default=str).encode("utf-8")
        return self._upload(f"reports/{scan_id}/report.json", content, "application/json")

    def _generate_markdown(self, scan_id: str, data: Dict) -> str:
        md = self._build_markdown(data)
        content = md.encode("utf-8")
        return self._upload(f"reports/{scan_id}/report.md", content, "text/markdown")

    def _build_markdown(self, data: Dict) -> str:
        decision = data.get("decision", "UNKNOWN")
        score = data.get("risk_score", 0)
        confidence = data.get("confidence", 0)
        contract = data.get("contract_address", "")
        chain = data.get("chain_id", 1)
        vulns = data.get("vulnerabilities", [])
        provenance = data.get("provenance", {})

        lines = [
            f"# ZauriScore Security Report",
            f"",
            f"**Contract:** `{contract}`  ",
            f"**Chain ID:** {chain}  ",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Risk Score | {score}/100 |",
            f"| Decision | **{decision}** |",
            f"| Confidence | {confidence}% |",
            f"| Static Analysis Score | {data.get('static_score', 0)} |",
            f"| Heuristic Score | {data.get('heuristic_score', 0)} |",
            f"| ML Score | {data.get('ml_score', 0)} |",
            f"",
            f"---",
            f"",
            f"## Vulnerabilities ({len(vulns)} found)",
            f"",
        ]

        for vuln in vulns:
            sev = vuln.get("severity", "unknown").upper()
            lines.append(f"### [{sev}] {vuln.get('detector', 'unknown')}")
            lines.append(f"")
            lines.append(f"**Description:** {vuln.get('description', '')}")
            lines.append(f"")
            if vuln.get("location"):
                lines.append(f"**Location:** `{vuln['location']}`")
                lines.append(f"")
            lines.append(f"**Source:** {vuln.get('source', 'unknown')}")
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

        lines += [
            f"## Provenance",
            f"",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Solc Version | {provenance.get('solc_version', 'unknown')} |",
            f"| Slither Version | {provenance.get('slither_version', 'unknown')} |",
            f"| Source Hash | `{provenance.get('source_hash', 'unknown')}` |",
            f"| Block Number | {provenance.get('block_number', 'unknown')} |",
            f"| Analysis Timestamp | {provenance.get('analysis_timestamp', 'unknown')} |",
            f"",
            f"---",
            f"",
            f"## Remediation",
            f"",
            self._remediation_advice(data),
            f"",
            f"---",
            f"",
            f"*Report generated by ZauriScore — AI-Powered Smart Contract Risk Intelligence*",
        ]

        return "\n".join(lines)

    def _remediation_advice(self, data: Dict) -> str:
        score = data.get("risk_score", 0)
        vulns = data.get("vulnerabilities", [])
        severities = [v.get("severity") for v in vulns]

        advice = []
        if "critical" in severities:
            advice.append("- **CRITICAL:** Address all critical vulnerabilities before deployment. These represent immediate security risks.")
        if "high" in severities:
            advice.append("- **HIGH:** Review and fix all high-severity issues. Consider a professional audit.")
        if score >= 70:
            advice.append("- Contract is **NOT recommended for deployment** in its current state.")
        elif score >= 40:
            advice.append("- Contract requires **security review** before deployment.")
        else:
            advice.append("- Contract appears relatively safe. Standard security practices apply.")

        advice.append("- Run additional tests with Echidna fuzzing for edge cases.")
        advice.append("- Consider a formal audit by a certified security firm for high-value contracts.")

        return "\n".join(advice)

    def _generate_pdf(self, scan_id: str, data: Dict) -> str:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
        story = self._build_pdf_story(data)
        doc.build(story)
        content = buffer.getvalue()
        return self._upload(f"reports/{scan_id}/report.pdf", content, "application/pdf")

    def _build_pdf_story(self, data: Dict) -> list:
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=24, spaceAfter=20)
        story.append(Paragraph("ZauriScore Security Report", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e40af")))
        story.append(Spacer(1, 12))

        # Contract info
        story.append(Paragraph(f"Contract: <font name='Courier'>{data.get('contract_address', 'N/A')}</font>", styles["Normal"]))
        story.append(Paragraph(f"Chain ID: {data.get('chain_id', 1)}", styles["Normal"]))
        story.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Summary table
        decision = data.get("decision", "UNKNOWN")
        dec_color = colors.HexColor(DECISION_COLORS.get(decision, "#6b7280"))
        score = data.get("risk_score", 0)

        summary_data = [
            ["Risk Score", "Decision", "Confidence"],
            [f"{score}/100", decision, f"{data.get('confidence', 0)}%"],
        ]
        t = Table(summary_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (1, 1), (1, 1), dec_color),
            ("TEXTCOLOR", (1, 1), (1, 1), colors.white),
            ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWHEIGHT", (0, 0), (-1, -1), 30),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Vulnerabilities
        vulns = data.get("vulnerabilities", [])
        story.append(Paragraph(f"Vulnerabilities ({len(vulns)} found)", styles["Heading2"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 8))

        if vulns:
            vuln_data = [["Severity", "Detector", "Description"]]
            for v in vulns[:20]:  # Limit for PDF
                vuln_data.append([
                    v.get("severity", "").upper(),
                    v.get("detector", ""),
                    v.get("description", "")[:80] + ("..." if len(v.get("description", "")) > 80 else ""),
                ])
            vt = Table(vuln_data, colWidths=[1 * inch, 1.5 * inch, 4 * inch])
            vt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f9fafb"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("WORDWRAP", (2, 1), (2, -1), True),
            ]))
            story.append(vt)
        else:
            story.append(Paragraph("No vulnerabilities detected.", styles["Normal"]))

        story.append(Spacer(1, 20))

        # Score breakdown
        story.append(Paragraph("Score Breakdown", styles["Heading2"]))
        score_data = [
            ["Component", "Score", "Weight", "Contribution"],
            ["Static Analysis (Slither)", f"{data.get('static_score', 0)}", "50%", f"{data.get('static_score', 0) * 0.5:.1f}"],
            ["Heuristic Engine", f"{data.get('heuristic_score', 0)}", "30%", f"{data.get('heuristic_score', 0) * 0.3:.1f}"],
            ["ML Risk Engine (CodeBERT)", f"{data.get('ml_score', 0)}", "20%", f"{data.get('ml_score', 0) * 0.2:.1f}"],
            ["TOTAL", f"{score}", "100%", f"{score}"],
        ]
        st = Table(score_data, colWidths=[2.5 * inch, 1.2 * inch, 1 * inch, 1.5 * inch])
        st.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#f9fafb"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story.append(st)
        story.append(Spacer(1, 30))

        story.append(Paragraph(
            "Report generated by ZauriScore — AI-Powered Smart Contract Risk Intelligence",
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#9ca3af"), alignment=TA_CENTER)
        ))

        return story


report_generator = ReportGenerator()
