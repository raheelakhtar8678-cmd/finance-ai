# src/visualization/report_builder.py

import os
from pathlib import Path
from datetime import datetime

# PDF tools
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# PPTX tools
from pptx import Presentation
from pptx.util import Inches, Pt


class PDFReportBuilder:
    """
    Generates a clean PDF report using:
      - KPIs
      - Text summary
      - Charts
    """

    def __init__(self, output_dir="reports/pdf"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        kpis: dict,
        trend_summary: str,
        chart_paths: list,
        filename="financial_report.pdf"
    ):
        pdf_path = self.output_dir / filename
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)

        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("<b>Financial Analysis Report</b>", styles["Title"]))
        story.append(Spacer(1, 20))

        # KPIs Table
        if kpis:
            story.append(Paragraph("<b>Key Performance Indicators (KPIs)</b>", styles["Heading2"]))

            table_data = [["KPI", "Value"]]
            for key, value in kpis.items():
                table_data.append([key, str(value)])

            table = Table(table_data)
            table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ])
            )
            story.append(table)
            story.append(Spacer(1, 20))

        # Trend Summary
        if trend_summary:
            story.append(Paragraph("<b>Trend Analysis Summary</b>", styles["Heading2"]))
            story.append(Paragraph(trend_summary, styles["BodyText"]))
            story.append(Spacer(1, 20))

        # Charts
        if chart_paths:
            story.append(Paragraph("<b>Charts</b>", styles["Heading2"]))
            for path in chart_paths:
                try:
                    story.append(Image(str(path), width=400, height=250))
                    story.append(Spacer(1, 20))
                except Exception:
                    pass

        doc.build(story)
        return str(pdf_path)


class PPTXReportBuilder:
    """
    Generates a professional PPTX report with:
      - KPIs slide
      - Trends slide
      - Each chart on its own slide
    """

    def __init__(self, output_dir="reports/pptx"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        kpis: dict,
        trend_summary: str,
        chart_paths: list,
        filename="financial_report.pptx"
    ):
        ppt_path = self.output_dir / filename
        prs = Presentation()

        # --- SLIDE 1: Title ---
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        title = slide.shapes.title
        subtitle = slide.placeholders[1]
        title.text = "Financial Analysis Report"
        subtitle.text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # --- SLIDE 2: KPIs ---
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        body = slide.placeholders[1]
        title.text = "Key Performance Indicators"

        kpi_text = "\n".join([f"{k}: {v}" for k, v in kpis.items()])
        body.text = kpi_text if kpis else "No KPIs detected."

        # --- SLIDE 3: Trend Summary ---
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        body = slide.placeholders[1]
        title.text = "Trend Analysis"
        body.text = trend_summary if trend_summary else "No trends detected."

        # --- SLIDES: CHARTS ---
        for chart in chart_paths:
            slide = prs.slides.add_slide(prs.slide_layouts[5])  # blank
            title = slide.shapes.title
            title.text = Path(chart).stem

            left = Inches(1.2)
            top = Inches(1.5)

            try:
                slide.shapes.add_picture(chart, left, top, width=Inches(7))
            except:
                pass

        prs.save(str(ppt_path))
        return str(ppt_path)