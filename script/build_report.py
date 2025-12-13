from src.visualization.report_builder import build_pdf_report
from src.visualization.chart_generator import ChartGenerator
from src.visualization.kpi_generator import generate_kpis_from_table

def assemble_report(tables, metrics):
    charts = []
    chart_gen = ChartGenerator("reports/charts")

    cleaned_map = {}
    for i, t in enumerate(tables):
        df = t["df"]
        cleaned_map[f"{t['source']}_{i}"] = df
        for col in df.select_dtypes("number").columns[:1]:
            charts.append(chart_gen.line_chart(df, col))

    return build_pdf_report(
        out_path="reports/final_report.pdf",
        title="Financial AI Report",
        cleaned_tables=cleaned_map,
        metrics=metrics,
        chart_paths=charts
    )