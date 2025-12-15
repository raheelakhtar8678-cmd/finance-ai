# src/analysis/metric_executor.py
"""
Smart metric execution with intelligent fallbacks and helpful error messages
"""

from src.analysis.calculator import safe_eval_expr
from src.ai.rag_engine import retrieve_context
from src.ai.variable_extractor import extract_variables_from_retrieved
import pandas as pd

# NEW IMPORT (Required for the updated functions)
from src.analysis.financial_reasoning import compute_metric_with_reasoning

# =============================================================================
# HELPER: Document Intelligence
# =============================================================================

def analyze_document_type(tables: list) -> dict:
    """
    Analyze what type of data is in the document.
    Returns helpful context for user.
    """
    all_columns = []
    sample_data = []
    
    for table_info in tables[:20]:  # Check first 20 tables
        df = table_info.get("df")
        if df is not None and not df.empty:
            all_columns.extend([str(col).lower() for col in df.columns])
            sample_data.append(df.head(2))
    
    # Detect document characteristics
    financial_keywords = ['revenue', 'profit', 'cash', 'expense', 'sales', 'cogs', 'income', 'assets', 'liabilities']
    research_keywords = ['date', 'name', 'charity', 'nursery', 'education', 'study']
    
    financial_matches = [kw for kw in financial_keywords if any(kw in col for col in all_columns)]
    research_matches = [kw for kw in research_keywords if any(kw in col for col in all_columns)]
    
    return {
        "is_financial": len(financial_matches) > 0,
        "is_research": len(research_matches) > 3,
        "columns_found": list(set(all_columns))[:10],
        "financial_columns": financial_matches,
        "total_tables": len(tables),
        "sample_columns": all_columns[:15] if all_columns else []
    }

def get_helpful_error_message(metric_name: str, tables: list, required_columns: list) -> str:
    """
    Generate a helpful error message that explains what WAS found
    instead of just saying 'insufficient data'
    """
    doc_analysis = analyze_document_type(tables)
    
    # Build helpful message
    msg_parts = [f"{metric_name.title()}: Unable to calculate"]
    
    # Explain why
    msg_parts.append(f"\nReason: Document doesn't contain required columns: {', '.join(required_columns)}")
    
    # Explain what WAS found
    if doc_analysis["is_financial"]:
        msg_parts.append(f"\nℹ️ Found financial data: {', '.join(doc_analysis['financial_columns'][:5])}")
        msg_parts.append("\nTry asking about these metrics instead.")
    elif doc_analysis["is_research"]:
        msg_parts.append("\nℹ️ This appears to be a research/academic document, not financial statements.")
        msg_parts.append("\nFor financial analysis, please upload:")
        msg_parts.append("  • 10-K/10-Q SEC filings")
        msg_parts.append("  • Income statements")
        msg_parts.append("  • Balance sheets")
        msg_parts.append("  • Cash flow statements")
    else:
        msg_parts.append(f"\nℹ️ Found {doc_analysis['total_tables']} tables with columns like:")
        msg_parts.append(f"  {', '.join(doc_analysis['sample_columns'][:8])}")
        msg_parts.append("\n\n💡 Try asking questions about the data that's actually present.")
    
    # Add what questions WOULD work
    if doc_analysis["columns_found"]:
        msg_parts.append(f"\n\n✅ You CAN ask about: {', '.join(doc_analysis['sample_columns'][:5])}")
    
    return ''.join(msg_parts)

# =============================================================================
# HELPER: Find Data in Tables
# =============================================================================

def find_column_in_tables(tables: list, column_keywords: list) -> tuple:
    """
    Search through tables to find a column matching any keyword.
    Returns: (dataframe, column_name) or (None, None)
    """
    for table_info in tables:
        df = table_info.get("df")
        if df is None or df.empty:
            continue
        
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in column_keywords:
                if keyword in col_lower:
                    return df, col
    
    return None, None

def extract_numeric_value(df, column, method='last'):
    """
    Extract a single numeric value from a column.
    Methods: 'last', 'mean', 'sum'
    """
    try:
        series = pd.to_numeric(df[column], errors='coerce').dropna()
        
        if series.empty:
            return None
        
        if method == 'last':
            return float(series.iloc[-1])
        elif method == 'mean':
            return float(series.mean())
        elif method == 'sum':
            return float(series.sum())
        else:
            return float(series.iloc[-1])
    except:
        return None

# =============================================================================
# INTENT-BASED METRIC EXECUTOR
# =============================================================================

def execute_metric(metric_config, df):
    """
    Finds variables in the dataframe based on metric_config and executes a formula.
    """
    variables = {}

    for col in df.columns:
        key = col.lower().replace(" ", "_")
        if key in metric_config.get("required_columns", []):
            try:
                variables[key] = df[col].dropna().astype(float).mean()
            except:
                continue

    if len(variables) < len(metric_config.get("required_columns", [])):
        raise ValueError("Insufficient data for metric")

    result = safe_eval_expr(metric_config["formula"], variables)
    return result, variables

# =============================================================================
# DIRECT METRIC FUNCTIONS (Updated with Reasoning Logic)
# =============================================================================

def burn_rate(tables: list) -> str:
    """Calculate burn rate with CFO-like reasoning"""
    result = compute_metric_with_reasoning("burn_rate", tables)
    
    if result["success"]:
        return f"Burn Rate: {result['result']:.1f} months runway\n\n{result['reasoning']}\n\nCalculation: {result['calculation']}\nConfidence: {result['confidence']:.0%}"
    else:
        return f"Burn Rate: {result['reasoning']}\n\nConfidence: {result['confidence']:.0%}"

def revenue_growth(tables: list) -> str:
    """Calculate revenue growth with CFO-like reasoning"""
    result = compute_metric_with_reasoning("revenue_growth", tables)
    
    if result["success"]:
        return f"Revenue Growth: {result['result']:+.1f}%\n\n{result['reasoning']}\n\nCalculation: {result['calculation']}\nConfidence: {result['confidence']:.0%}"
    else:
        return f"Revenue Growth: {result['reasoning']}\n\nConfidence: {result['confidence']:.0%}"

def gross_margin(tables: list) -> str:
    """Calculate gross margin with CFO-like reasoning"""
    result = compute_metric_with_reasoning("gross_margin", tables)
    
    if result["success"]:
        return f"Gross Margin: {result['result']:.1f}%\n\n{result['reasoning']}\n\nCalculation: {result['calculation']}\nConfidence: {result['confidence']:.0%}"
    else:
        return f"Gross Margin: {result['reasoning']}\n\nConfidence: {result['confidence']:.0%}"

def net_profit_margin(tables: list) -> str:
    """Calculate net profit margin with CFO-like reasoning"""
    result = compute_metric_with_reasoning("net_profit_margin", tables)
    
    if result["success"]:
        return f"Net Profit Margin: {result['result']:.1f}%\n\n{result['reasoning']}\n\nCalculation: {result['calculation']}\nConfidence: {result['confidence']:.0%}"
    else:
        return f"Net Profit Margin: {result['reasoning']}\n\nConfidence: {result['confidence']:.0%}"

# =============================================================================
# UNIVERSAL QUESTION HANDLER (For any question about the data)
# =============================================================================

def answer_general_question(question: str, tables: list) -> str:
    """
    Handles any question about the document using RAG.
    Falls back when specific metrics can't be calculated.
    """
    try:
        # Use RAG to find relevant information
        contexts = retrieve_context(question, k=10)
        
        if not contexts:
            doc_analysis = analyze_document_type(tables)
            return f"I couldn't find information about '{question}' in this document.\n\nℹ️ Available data includes:\n  {', '.join(doc_analysis['sample_columns'][:8])}"
    
        # Extract key information from contexts
        relevant_info = []
        for ctx in contexts[:3]:
            text = ctx.get('text', '')
            if text and len(text.strip()) > 20:
                relevant_info.append(text[:150])
        
        if relevant_info:
            response = f"Based on the document:\n\n"
            for i, info in enumerate(relevant_info, 1):
                response += f"{i}. {info}\n"
            return response
        else:
            return "I found some related data, but it's not clear enough to answer your question. Could you be more specific?"
            
    except Exception as e:
        return f"Error processing question: {str(e)}"


# =============================================================================
# REGISTRY
# =============================================================================

AVAILABLE_METRICS = {
    "burn_rate": burn_rate,
    "revenue_growth": revenue_growth,
    "gross_margin": gross_margin,
    "net_profit_margin": net_profit_margin,
}