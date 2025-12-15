# src/analysis/query_controller.py

from src.analysis.question_router import resolve_intent
from src.analysis.table_resolver import find_relevant_tables
from src.analysis.metric_executor import execute_metric
from src.visualization.chart_router import generate_metric_chart
from src.ai.answer_generator import generate_answer

# Direct metric registry
from src.analysis.metric_registry import METRIC_REGISTRY_FUNCTIONS

# ✅ ADD THIS IMPORT
from src.analysis.comparison_engine import is_comparison_query, compare_across_documents


# -------------------------------------------------
# 1️⃣ Direct Metric Handler (FAST PATH)
# -------------------------------------------------
def handle_query(query: str, tables):
    """Executes a metric directly if its name is found in the query"""
    for metric_name, metric_fn in METRIC_REGISTRY_FUNCTIONS.items():
        if metric_name.lower() in query.lower():
            return metric_fn(tables)
    return None


# -------------------------------------------------
# 2️⃣ Intent-Based Reasoning Pipeline
# -------------------------------------------------
def answer_query(question, cleaned_tables, chart_gen):
    """Full reasoning pipeline"""
    
    # 1. Resolve intent
    metric_name, config = resolve_intent(question)
    if not metric_name:
        return "Unable to identify financial intent.", None

    # 2. Find relevant tables
    tables = find_relevant_tables(cleaned_tables, config["required_columns"])
    if not tables:
        return "No relevant financial tables found.", None

    # 3. Use first relevant table
    filename, idx, df = tables[0]

    # 4. Execute metric
    result, variables = execute_metric(config, df)

    # 5. Generate chart (if applicable)
    chart = generate_metric_chart(chart_gen, df, metric_name)

    # 6. Generate answer
    answer = generate_answer(metric_name, result, variables)

    return answer, chart


# -------------------------------------------------
# 3️⃣ Unified Router (ENTRY POINT) - ✅ UPDATED WITH C-4
# -------------------------------------------------
def route_query(question, cleaned_tables, chart_gen):
    """
    Unified query router:
    1) Check if comparison query → C-4
    2) Try direct metric execution → C-3
    3) Fallback to intent-based reasoning
    """
    
    # ✅ NEW: Check for comparison intent first (C-4)
    if is_comparison_query(question):
        comparison_result = compare_across_documents(question, cleaned_tables)
        
        if comparison_result.get("success"):
            return (
                f"Comparison Result:\n\n{comparison_result['summary']}\n\nConfidence: {comparison_result['confidence']:.0%}",
                None  # Charts handled separately if needed
            )
        else:
            # Comparison failed, try other approaches
            pass

    # Attempt direct metric execution (existing)
    direct_result = handle_query(question, cleaned_tables)
    if direct_result is not None:
        return (
            f"Computed result for '{question}': {direct_result}",
            None
        )

    # Fallback to full reasoning pipeline (existing)
    return answer_query(question, cleaned_tables, chart_gen)