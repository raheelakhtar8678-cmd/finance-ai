# query_controller.py

from src.analysis.question_router import resolve_intent
from src.analysis.table_resolver import find_relevant_tables
from src.analysis.metric_executor import execute_metric
from src.visualization.chart_router import generate_metric_chart
from src.ai.answer_generator import generate_answer
# Import the METRIC_REGISTRY_FUNCTIONS which holds executable functions
from src.analysis.metric_registry import METRIC_REGISTRY_FUNCTIONS 

# --- New Function ---
def handle_query(query: str, tables):
    """
    Executes a metric directly if its name is found in the query 
    by looking up the executable function in the METRIC_REGISTRY_FUNCTIONS.
    """
    for metric_name, metric_fn in METRIC_REGISTRY_FUNCTIONS.items():
        # Check if the full metric name is in the query (case-insensitive)
        if metric_name.lower() in query.lower():
            # Execute the function, assuming it takes 'tables' as an argument
            return metric_fn(tables)
    return None

# --- Original Answer Query Function ---
def answer_query(question, cleaned_tables, chart_gen):
    
    # 1. Resolve Intent
    metric_name, config = resolve_intent(question)

    if not metric_name:
        return "Unable to identify financial intent.", None

    # 2. Find Relevant Tables
    tables = find_relevant_tables(cleaned_tables, config["required_columns"])

    if not tables:
        return "No relevant financial tables found.", None

    # 3. Use the first relevant table found
    filename, idx, df = tables[0]

    # 4. Execute Metric and Generate Chart
    result, variables = execute_metric(config, df)
    chart = generate_metric_chart(chart_gen, df, metric_name)

    # 5. Generate Final Answer
    answer = generate_answer(metric_name, result, variables)

    # Return the generated answer and chart object
    return answer, chart