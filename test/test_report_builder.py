# test/test_report_builder.py
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import tempfile

from src.visualization.report_builder import build_pdf_report, build_pptx_report

def _create_dummy_chart(path: Path):
    fig, ax = plt.subplots()
    ax.plot([1,2,3], [10, 20, 15], marker='o')
    ax.set_title("Dummy Chart")
    fig.savefig(str(path))
    plt.close(fig)

def test_build_reports(tmp_path):
    # Prepare dummy cleaned tables
    df = pd.DataFrame({
        "Revenue": [1000, 1200, 1300],
        "Cost": [600, 700, 650]
    })
    cleaned = {"income_statement": df}

    # metrics
    metrics = {"revenue_latest": 1300, "gross_margin": 0.5}

    # create chart
    chart_path = tmp_path / "chart.png"
    _create_dummy_chart(chart_path)

    # pdf
    pdf_out = tmp_path / "report.pdf"
    pdf_path = build_pdf_report(
        out_path=pdf_out,
        title="Test Report",
        cleaned_tables=cleaned,
        metrics=metrics,
        chart_paths=[str(chart_path)],
        author="unit-test"
    )
    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 0

    # pptx
    pptx_out = tmp_path / "report.pptx"
    pptx_path = build_pptx_report(
        out_path=pptx_out,
        title="Test PPTX",
        cleaned_tables=cleaned,
        metrics=metrics,
        chart_paths=[str(chart_path)],
        author="unit-test"
    )
    assert Path(pptx_path).exists()
    assert Path(pptx_path).stat().st_size > 0