"""
Professional PDF Report Generator for PredictV.

Creates detailed diagnostic reports using ReportLab with:
- Cover page, emission tables, health gauges, charts
- Fault analysis, recommendations, maintenance schedules
- Professional formatting with colors and branding
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Color Palette
DARK_BG = colors.HexColor("#0f172a")
PRIMARY = colors.HexColor("#3b82f6")
SUCCESS = colors.HexColor("#22c55e")
WARNING = colors.HexColor("#eab308")
DANGER = colors.HexColor("#ef4444")
ORANGE = colors.HexColor("#f97316")
GRAY = colors.HexColor("#64748b")
LIGHT_GRAY = colors.HexColor("#e2e8f0")
WHITE = colors.white
BLACK = colors.HexColor("#1e293b")


def get_health_color(score: float) -> colors.HexColor:
    """Get color based on health score."""
    if score >= 85:
        return SUCCESS
    elif score >= 70:
        return colors.HexColor("#84cc16")
    elif score >= 50:
        return WARNING
    elif score >= 30:
        return ORANGE
    return DANGER


def get_compliance_color(status: str) -> colors.HexColor:
    """Get color based on compliance status."""
    return {"Pass": SUCCESS, "Warning": WARNING, "Fail": DANGER}.get(status, GRAY)


class ReportGenerator:
    """Generates professional PDF diagnostic reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            "ReportTitle", parent=self.styles["Title"],
            fontSize=28, leading=34, textColor=PRIMARY, spaceAfter=20,
        ))
        self.styles.add(ParagraphStyle(
            "SectionHeader", parent=self.styles["Heading1"],
            fontSize=16, leading=22, textColor=PRIMARY, spaceAfter=10,
            spaceBefore=20, borderWidth=0, borderPadding=0,
        ))
        self.styles.add(ParagraphStyle(
            "SubHeader", parent=self.styles["Heading2"],
            fontSize=12, leading=16, textColor=BLACK, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "BodyText", parent=self.styles["Normal"],
            fontSize=10, leading=14, textColor=BLACK, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "SmallText", parent=self.styles["Normal"],
            fontSize=8, leading=10, textColor=GRAY,
        ))
        self.styles.add(ParagraphStyle(
            "CenterText", parent=self.styles["Normal"],
            fontSize=10, leading=14, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "ScoreText", parent=self.styles["Normal"],
            fontSize=48, leading=56, alignment=TA_CENTER, textColor=PRIMARY,
        ))

    def generate(self, data: Dict[str, Any], output_path: str) -> str:
        """Generate the complete PDF report."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        story = []
        story.extend(self._build_cover_page(data))
        story.append(PageBreak())
        story.extend(self._build_summary_section(data))
        story.extend(self._build_health_section(data))
        story.extend(self._build_emission_section(data))
        story.extend(self._build_fault_section(data))
        story.append(PageBreak())
        story.extend(self._build_rul_section(data))
        story.extend(self._build_forecast_section(data))
        story.extend(self._build_recommendations_section(data))
        story.extend(self._build_maintenance_section(data))
        story.extend(self._build_notes_section(data))
        story.extend(self._build_footer_section(data))

        doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        return output_path

    def _header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()
        # Footer
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRAY)
        canvas.drawString(
            2 * cm, 1 * cm,
            f"PredictV Diagnostic Report | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | Confidential"
        )
        canvas.drawRightString(
            A4[0] - 2 * cm, 1 * cm,
            f"Page {doc.page}"
        )
        # Top line
        canvas.setStrokeColor(PRIMARY)
        canvas.setLineWidth(2)
        canvas.line(2 * cm, A4[1] - 1.2 * cm, A4[0] - 2 * cm, A4[1] - 1.2 * cm)
        canvas.restoreState()

    def _build_cover_page(self, data: Dict) -> List:
        """Build the cover page."""
        elements = []
        elements.append(Spacer(1, 4 * cm))
        elements.append(Paragraph("PredictV", self.styles["ReportTitle"]))
        elements.append(Paragraph("AI Vehicle Diagnostic Report", self.styles["SectionHeader"]))
        elements.append(Spacer(1, 1 * cm))
        elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
        elements.append(Spacer(1, 1 * cm))

        vehicle = data.get("vehicle", {})
        info_data = [
            ["Report Number:", data.get("report_number", "N/A")],
            ["Vehicle:", f"{vehicle.get('year', '')} {vehicle.get('brand', '')} {vehicle.get('model', '')}"],
            ["Engine:", f"{vehicle.get('engine_capacity', '')}L {vehicle.get('fuel_type', '').upper()}"],
            ["Mileage:", f"{vehicle.get('mileage', 0):,.0f} km"],
            ["VIN:", vehicle.get("vin", "N/A")],
            ["Date:", datetime.now().strftime("%B %d, %Y")],
        ]

        table = Table(info_data, colWidths=[4 * cm, 12 * cm])
        table.setStyle(TableStyle([
            ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 11),
            ("FONT", (1, 0), (1, -1), "Helvetica", 11),
            ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
            ("TEXTCOLOR", (1, 0), (1, -1), BLACK),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)

        elements.append(Spacer(1, 2 * cm))

        # Quick status badges
        health = data.get("health_score", 0)
        compliance = data.get("emission_compliance", "N/A")
        risk = data.get("risk_level", "N/A")

        status_data = [
            ["Health Score", "Compliance", "Risk Level"],
            [
                f"{health:.0f}/100",
                compliance,
                risk,
            ],
        ]
        status_table = Table(status_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
        status_table.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
            ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 18),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRAY),
            ("TEXTCOLOR", (0, 1), (0, 1), get_health_color(health)),
            ("TEXTCOLOR", (1, 1), (1, 1), get_compliance_color(compliance)),
            ("TEXTCOLOR", (2, 1), (2, 1), DANGER if risk == "Critical" else (ORANGE if risk == "High" else (WARNING if risk == "Medium" else SUCCESS))),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        elements.append(status_table)

        return elements

    def _build_summary_section(self, data: Dict) -> List:
        """Build executive summary section."""
        elements = []
        elements.append(Paragraph("Executive Summary", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        health = data.get("health_score", 0)
        classification = data.get("health_classification", "N/A")
        confidence = data.get("overall_confidence", 0)

        summary_text = (
            f"This diagnostic report analyzes the engine health and emission characteristics "
            f"of the vehicle. The overall engine health score is <b>{health:.1f}/100</b> "
            f"({classification}) with a confidence level of <b>{confidence * 100:.0f}%</b>. "
            f"The emission compliance status is <b>{data.get('emission_compliance', 'N/A')}</b>."
        )
        elements.append(Paragraph(summary_text, self.styles["BodyText"]))

        fault_count = len(data.get("detected_faults", []))
        if fault_count > 0:
            elements.append(Paragraph(
                f"<b>{fault_count} potential issue(s)</b> were detected during analysis. "
                f"Please review the fault analysis section for details.",
                self.styles["BodyText"],
            ))

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_health_section(self, data: Dict) -> List:
        """Build the health score section."""
        elements = []
        elements.append(Paragraph("Engine Health Assessment", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        health = data.get("health_score", 0)
        color = get_health_color(health)

        health_data = [
            ["Health Score", "Classification", "Confidence", "Risk Level"],
            [
                f"{health:.1f}",
                data.get("health_classification", "N/A"),
                f"{data.get('overall_confidence', 0) * 100:.0f}%",
                data.get("risk_level", "N/A"),
            ],
        ]
        ht = Table(health_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
        ht.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("FONT", (0, 1), (-1, 1), "Helvetica-Bold", 14),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRAY),
            ("TEXTCOLOR", (0, 1), (0, 1), color),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(ht)

        # Additional ratings
        ratings_data = [
            ["Fuel Efficiency", "Environmental Impact", "Emission Rating"],
            [
                f"{data.get('fuel_efficiency_rating', 0):.0f}/100",
                f"{data.get('environmental_impact_score', 0):.0f}/100",
                data.get("emission_rating", "N/A"),
            ],
        ]
        rt = Table(ratings_data, colWidths=[5.3 * cm, 5.3 * cm, 5.3 * cm])
        rt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("FONT", (0, 1), (-1, 1), "Helvetica", 12),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRAY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(Spacer(1, 3 * mm))
        elements.append(rt)
        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_emission_section(self, data: Dict) -> List:
        """Build emission test results table."""
        elements = []
        elements.append(Paragraph("Emission Test Results", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            f"Compliance Status: <b>{data.get('emission_compliance', 'N/A')}</b>",
            self.styles["BodyText"],
        ))
        elements.append(Spacer(1, 3 * mm))
        return elements

    def _build_fault_section(self, data: Dict) -> List:
        """Build detected faults section."""
        elements = []
        faults = data.get("detected_faults", [])
        elements.append(Paragraph(f"Fault Analysis ({len(faults)} detected)", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        if not faults:
            elements.append(Paragraph("✅ No significant faults detected.", self.styles["BodyText"]))
            elements.append(Spacer(1, 5 * mm))
            return elements

        fault_table_data = [["#", "Fault", "Probability", "Severity", "Est. Cost"]]
        for i, fault in enumerate(faults[:10], 1):
            if isinstance(fault, dict):
                fault_table_data.append([
                    str(i),
                    fault.get("fault", "Unknown"),
                    f"{fault.get('probability', 0) * 100:.0f}%",
                    fault.get("severity", "N/A").title(),
                    f"${fault.get('estimated_repair_cost', 0):,.0f}",
                ])

        if len(fault_table_data) > 1:
            ft = Table(fault_table_data, colWidths=[1 * cm, 6 * cm, 3 * cm, 3 * cm, 3 * cm])
            ft.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
                ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafc")]),
            ]))
            elements.append(ft)

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_rul_section(self, data: Dict) -> List:
        """Build remaining useful life section."""
        elements = []
        elements.append(Paragraph("Remaining Useful Life", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        rul_data = [
            ["Metric", "Value"],
            ["Remaining Engine Life", f"{data.get('remaining_life_km', 0):,.0f} km"],
            ["Distance to Next Maintenance", f"{data.get('km_to_maintenance', 0):,.0f} km"],
            ["Breakdown Probability", f"{(data.get('breakdown_probability', 0) or 0) * 100:.1f}%"],
            ["Estimated Repair Cost", f"${data.get('estimated_repair_cost_min', 0):,.0f} – ${data.get('estimated_repair_cost_max', 0):,.0f}"],
        ]

        rt = Table(rul_data, colWidths=[8 * cm, 8 * cm])
        rt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
            ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 9),
            ("FONT", (1, 1), (1, -1), "Helvetica", 9),
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(rt)
        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_forecast_section(self, data: Dict) -> List:
        """Build predictive analytics section."""
        elements = []
        elements.append(Paragraph("Predictive Analytics", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        forecasts = data.get("forecasts", [])
        if not forecasts:
            elements.append(Paragraph("No forecast data available.", self.styles["BodyText"]))
            return elements

        forecast_data = [["Horizon", "Health Score", "Degradation", "Risk", "Est. Cost"]]
        for f in forecasts:
            if isinstance(f, dict) and f:
                horizon = f.get("horizon", f.get("horizon_days", ""))
                if isinstance(horizon, int):
                    horizon = f"{horizon}d" if horizon < 365 else "1y"
                forecast_data.append([
                    str(horizon),
                    f"{f.get('health_score', 0):.1f}",
                    f"{f.get('engine_degradation_pct', 0):.1f}%",
                    f"{f.get('risk_score', 0) * 100:.0f}%",
                    f"${f.get('maintenance_cost', 0):,.0f}",
                ])

        if len(forecast_data) > 1:
            ft = Table(forecast_data, colWidths=[3 * cm, 3.5 * cm, 3 * cm, 3 * cm, 3.5 * cm])
            ft.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
                ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(ft)

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_recommendations_section(self, data: Dict) -> List:
        """Build recommendations section."""
        elements = []
        recs = data.get("recommendations", [])
        elements.append(Paragraph(f"Recommendations ({len(recs)})", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        for i, rec in enumerate(recs, 1):
            if isinstance(rec, dict):
                priority = rec.get("priority", "Medium")
                pcolor = {"Critical": DANGER, "High": ORANGE, "Medium": WARNING, "Low": SUCCESS}.get(priority, GRAY)
                elements.append(Paragraph(
                    f"<b>{i}. {rec.get('title', 'Recommendation')}</b> "
                    f"[<font color='{pcolor}'>{priority}</font>]",
                    self.styles["BodyText"],
                ))
                elements.append(Paragraph(
                    f"  {rec.get('description', '')} "
                    f"— Estimated cost: ${rec.get('estimated_cost', 0):,.0f}",
                    self.styles["SmallText"],
                ))
                elements.append(Spacer(1, 2 * mm))

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_maintenance_section(self, data: Dict) -> List:
        """Build maintenance schedule section."""
        elements = []
        schedule = data.get("maintenance_schedule", [])
        elements.append(Paragraph("Maintenance Schedule", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        if not schedule:
            elements.append(Paragraph("No scheduled maintenance.", self.styles["BodyText"]))
            return elements

        sched_data = [["Service", "Interval", "Next Due", "Priority"]]
        for item in schedule:
            if isinstance(item, dict):
                sched_data.append([
                    item.get("service", ""),
                    f"{item.get('interval_km', 0):,} km",
                    f"{item.get('next_due_km', 0):,} km",
                    item.get("priority", "Medium"),
                ])

        if len(sched_data) > 1:
            st = Table(sched_data, colWidths=[6 * cm, 3.5 * cm, 3.5 * cm, 3 * cm])
            st.setStyle(TableStyle([
                ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("BOX", (0, 0), (-1, -1), 1, LIGHT_GRAY),
                ("GRID", (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(st)

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_notes_section(self, data: Dict) -> List:
        """Build technician notes section."""
        elements = []
        notes = data.get("technician_notes", "")
        elements.append(Paragraph("Technician Notes", self.styles["SectionHeader"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
        elements.append(Spacer(1, 5 * mm))

        if notes:
            elements.append(Paragraph(notes, self.styles["BodyText"]))
        else:
            elements.append(Paragraph("<i>No technician notes provided.</i>", self.styles["SmallText"]))

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _build_footer_section(self, data: Dict) -> List:
        """Build report footer with disclaimer."""
        elements = []
        elements.append(Spacer(1, 1 * cm))
        elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph(
            "<b>Disclaimer:</b> This report is generated by PredictV AI diagnostic system. "
            "The predictions and recommendations are based on the provided emission data and "
            "sensor readings. Actual engine conditions may vary. Always consult a qualified "
            "technician for definitive diagnosis and repairs.",
            self.styles["SmallText"],
        ))
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(
            f"© {datetime.now().year} PredictV — AI Vehicle Diagnostic System | All Rights Reserved",
            ParagraphStyle("Footer", parent=self.styles["SmallText"], alignment=TA_CENTER),
        ))
        return elements
