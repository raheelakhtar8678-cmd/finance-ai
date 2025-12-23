# src/analysis/query_controller.py
"""
Flexible Query Controller - Answers ANYTHING about uploaded documents
Uses: Deterministic → RAG → LLM chain with chart generation
"""

from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.visualization.chart_generator import generate_chart as gen_chart
from src.ai.answer_generator import generate_answer
from src.analysis.question_router import resolve_intent
from src.ai.rag_engine import retrieve_context
from src.ai.llm_narrator import LLMNarrator
import pandas as pd


def route_query(question, cleaned_tables, chart_gen=None):
    """
    Universal query router - answers ANY question about uploaded documents.
    
    Flow:
    1. Try predefined metrics (burn rate, revenue growth, etc.)
    2. If fails, use RAG to find relevant data
    3. Let LLM read the actual data and answer freely
    4. Generate charts for any numeric trends found
    
    Args:
        question: User's question (can be anything!)
        cleaned_tables: List of dicts with {"df": df, "source": name}
        chart_gen: Optional chart generator
    
    Returns:
        (answer, chart_path)
    """
    
    print(f"\n🔍 Processing question: {question}")
    
    # ==========================================
    # LAYER 1: TRY PREDEFINED METRICS
    # ==========================================
    metric_name, config = resolve_intent(question)
    
    if metric_name:
        print(f"🎯 Detected predefined metric: {metric_name}")
        
        # Try deterministic calculation
        reasoned_data = compute_metric_with_reasoning(metric_name, cleaned_tables)
        
        if reasoned_data.get("success"):
            print(f"✅ Metric calculated successfully")
            
            # Generate chart
            chart_path = try_generate_chart(metric_name, cleaned_tables, reasoned_data)
            
            # Generate answer with LLM
            answer = generate_answer_with_llm(
                question=question,
                reasoned_data=reasoned_data,
                chart_path=chart_path,
                tables=cleaned_tables
            )
            
            return answer, chart_path
        else:
            print(f"⚠️ Calculation failed: {reasoned_data.get('reasoning')}")
            # Continue to RAG fallback below
    
    # ==========================================
    # LAYER 2: RAG + LLM - ANSWER ANYTHING
    # ==========================================
    print("🔍 No exact metric or calculation failed - using RAG + LLM to answer")
    
    # Retrieve relevant context from documents
    rag_contexts = retrieve_context(question, k=10)
    
    # Build comprehensive context from RAG
    rag_text = build_rag_context(rag_contexts)
    
    # Build table summary for LLM
    table_summary = build_table_summary(cleaned_tables)
    
    # Try to find relevant numeric data for charting
    chart_path = try_smart_chart(question, cleaned_tables)
    
    # Let LLM answer freely using all available data
    narrator = LLMNarrator()
    
    full_prompt = f"""
You are a senior financial analyst. Answer the user's question based on the uploaded documents.

User Question: {question}

Document Data (RAG Context):
{rag_text}

Available Tables Summary:
{table_summary}

{'A trend chart has been generated and is available.' if chart_path else 'No chart available.'}

Instructions:
- Answer the question directly and specifically
- Use actual numbers from the context when available
- If asking about profit/loss, check for negative numbers
- If asking about trends, describe what you see in the data
- If asking about specific items, search the context for them
- Be conversational and helpful
- If you truly cannot find the answer, explain what data IS available

Provide a clear, professional answer.
"""
    
    try:
        answer = narrator.explain(
            user_question=question,
            rag_context=rag_text,
            computed_result=table_summary,
            charts=[chart_path] if chart_path else None
        )
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        answer = f"I found information in your documents but encountered an error generating the explanation. Here's what I found:\n\n{rag_text[:500]}..."
    
    return answer, chart_path


def try_generate_chart(metric_name, tables, reasoned_data):
    """Try to generate chart for a calculated metric"""
    try:
        # If reasoning data includes dataframe and column
        if "df" in reasoned_data and "col" in reasoned_data:
            df = reasoned_data["df"]
            col = reasoned_data["col"]
            
            result = gen_chart(
                df=df,
                x_col=df.columns[0] if len(df.columns) > 0 else None,
                y_col=col,
                title=f"{metric_name.replace('_', ' ').title()}",
                output_path=f"data/static/{metric_name}.png"
            )
            
            if result.get("image_path"):
                return result["image_path"]
    except Exception as e:
        print(f"⚠️ Chart generation failed: {e}")
    
    return None


def try_smart_chart(question, tables):
    """
    Smart chart generation based on question keywords
    Looks for numeric columns mentioned in the question
    """
    
    if not tables:
        return None
    
    # Extract potential column names from question
    question_lower = question.lower()
    chart_keywords = {
        "revenue": ["revenue", "sales", "income"],
        "profit": ["profit", "earnings", "net income"],
        "expenses": ["expenses", "costs", "spending"],
        "cash": ["cash", "balance", "liquidity"],
        "growth": ["growth", "trend", "change"]
    }
    
    # Try to find matching columns
    for table_dict in tables:
        df = table_dict["df"]
        
        for concept, keywords in chart_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    # Look for matching column
                    for col in df.columns:
                        if keyword in str(col).lower():
                            try:
                                result = gen_chart(
                                    df=df,
                                    x_col=df.columns[0],
                                    y_col=col,
                                    title=f"{col} Trend",
                                    output_path=f"data/static/smart_chart.png"
                                )
                                if result.get("image_path"):
                                    return result["image_path"]
                            except:
                                continue
    
    return None


def build_rag_context(rag_contexts):
    """Build formatted context from RAG retrieval"""
    
    if not rag_contexts:
        return "No specific context retrieved from documents."
    
    context_parts = []
    for idx, ctx in enumerate(rag_contexts[:5], 1):  # Top 5 results
        source = ctx.get("source", "Unknown")
        text = ctx.get("text", "")
        context_parts.append(f"[Source {idx}: {source}]\n{text}")
    
    return "\n\n".join(context_parts)


def build_table_summary(tables):
    """Build summary of available tables and columns"""
    
    if not tables:
        return "No tables available."
    
    summary_parts = []
    # src/analysis/query_controller.py
"""
Flexible Query Controller - Answers ANYTHING about uploaded documents
Uses: Deterministic → RAG → LLM chain with chart generation
"""

from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.visualization.chart_generator import generate_chart as gen_chart
from src.ai.answer_generator import generate_answer
from src.analysis.question_router import resolve_intent
from src.ai.rag_engine import retrieve_context
from src.ai.llm_narrator import LLMNarrator
import pandas as pd


def route_query(question, cleaned_tables, chart_gen=None):
    """
    Universal query router - answers ANY question about uploaded documents.
    
    Flow:
    1. Try predefined metrics (burn rate, revenue growth, etc.)
    2. If fails, use RAG to find relevant data
    3. Let LLM read the actual data and answer freely
    4. Generate charts for any numeric trends found
    
    Args:
        question: User's question (can be anything!)
        cleaned_tables: List of dicts with {"df": df, "source": name}
        chart_gen: Optional chart generator
    
    Returns:
        (answer, chart_path)
    """
    
    print(f"\n🔍 Processing question: {question}")
    
    # ==========================================
    # LAYER 1: TRY PREDEFINED METRICS
    # ==========================================
    metric_name, config = resolve_intent(question)
    
    if metric_name:
        print(f"🎯 Detected predefined metric: {metric_name}")
        
        # Try deterministic calculation (chart is generated inside reasoning)
        reasoned_data = compute_metric_with_reasoning(metric_name, cleaned_tables)
        
        if reasoned_data.get("success"):
            print(f"✅ Metric calculated successfully")
            
            # Chart already generated by reasoning engine
            chart_path = reasoned_data.get("chart_path")
            
            # Generate answer with LLM
            answer = generate_answer_with_llm(
                question=question,
                reasoned_data=reasoned_data,
                chart_path=chart_path,
                tables=cleaned_tables
            )
            
            return answer, chart_path
        else:
            print(f"⚠️ Calculation failed: {reasoned_data.get('reasoning')}")
            # Continue to RAG fallback below
    
    # ==========================================
    # LAYER 2: RAG + LLM - ANSWER ANYTHING
    # ==========================================
    print("🔍 No exact metric or calculation failed - using RAG + LLM to answer")
    
    # Retrieve relevant context from documents
    rag_contexts = retrieve_context(question, k=10)
    
    # Build comprehensive context from RAG
    rag_text = build_rag_context(rag_contexts)
    
    # Build table summary for LLM
    table_summary = build_table_summary(cleaned_tables)
    
    # Try to find relevant numeric data for charting
    chart_path = try_smart_chart(question, cleaned_tables)
    
    # Let LLM answer freely using all available data
    narrator = LLMNarrator()
    
    full_prompt = f"""
You are a senior financial analyst. Answer the user's question based on the uploaded documents.

User Question: {question}

Document Data (RAG Context):
{rag_text}

Available Tables Summary:
{table_summary}

{'A trend chart has been generated and is available.' if chart_path else 'No chart available.'}

Instructions:
- Answer the question directly and specifically
- Use actual numbers from the context when available
- If asking about profit/loss, check for negative numbers
- If asking about trends, describe what you see in the data
- If asking about specific items, search the context for them
- Be conversational and helpful
- If you truly cannot find the answer, explain what data IS available

Provide a clear, professional answer.
"""
    
    try:
        answer = narrator.explain(
            user_question=question,
            rag_context=rag_text,
            computed_result=table_summary,
            charts=[chart_path] if chart_path else None
        )
    except Exception as e:
        print(f"❌ LLM generation failed: {e}")
        answer = f"I found information in your documents but encountered an error generating the explanation. Here's what I found:\n\n{rag_text[:500]}..."
    
    return answer, chart_path


def try_generate_chart(metric_name, tables, reasoned_data):
    """
    Deprecated - Charts now generated inside financial_reasoning.py
    Keeping for backward compatibility
    """
    return reasoned_data.get("chart_path")


def try_smart_chart(question, tables):
    """
    Smart chart generation for RAG fallback queries.
    Uses your existing chart_generator.py
    """
    
    if not tables:
        return None
    
    from src.visualization.chart_generator import generate_chart
    from pathlib import Path
    
    # Extract potential column names from question
    question_lower = question.lower()
    chart_keywords = {
        "revenue": ["revenue", "sales", "income"],
        "profit": ["profit", "earnings", "net income"],
        "expenses": ["expenses", "costs", "spending"],
        "cash": ["cash", "balance", "liquidity"],
    }
    
    # Try to find matching columns
    for table_dict in tables:
        df = table_dict["df"]
        
        for concept, keywords in chart_keywords.items():
            for keyword in keywords:
                if keyword in question_lower:
                    # Look for matching column
                    for col in df.columns:
                        if keyword in str(col).lower() and pd.api.types.is_numeric_dtype(df[col]):
                            try:
                                # Find x-axis column
                                x_col = None
                                for potential_x in df.columns:
                                    if potential_x != col:
                                        x_col = potential_x
                                        break
                                
                                if x_col is None:
                                    x_col = df.columns[0]
                                
                                # Generate chart
                                output_path = f"data/static/smart_chart_{concept}.png"
                                Path("data/static").mkdir(parents=True, exist_ok=True)
                                
                                result = generate_chart(
                                    df=df,
                                    x_col=x_col,
                                    y_col=col,
                                    title=f"{col} Trend",
                                    output_path=output_path
                                )
                                
                                if result.get("success"):
                                    return result["image_path"]
                            except Exception as e:
                                print(f"⚠️ Chart generation error: {e}")
                                continue
    
    return None


def build_rag_context(rag_contexts):
    """Build formatted context from RAG retrieval"""
    
    if not rag_contexts:
        return "No specific context retrieved from documents."
    
    context_parts = []
    for idx, ctx in enumerate(rag_contexts[:5], 1):  # Top 5 results
        source = ctx.get("source", "Unknown")
        text = ctx.get("text", "")
        context_parts.append(f"[Source {idx}: {source}]\n{text}")
    
    return "\n\n".join(context_parts)


def build_table_summary(tables):
    """Build summary of available tables and columns"""
    
    if not tables:
        return "No tables available."
    
    summary_parts = []
    
    for idx, table_dict in enumerate(tables[:3], 1):  # First 3 tables
        df = table_dict["df"]
        source = table_dict.get("source", f"Table {idx}")
        
        # Get column info
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        summary = f"Table {idx} ({source}):\n"
        summary += f"  Rows: {len(df)}\n"
        
        if numeric_cols:
            summary += f"  Numeric columns: {', '.join(numeric_cols[:5])}\n"
            
            # Show sample values
            for col in numeric_cols[:3]:
                sample_val = df[col].iloc[0] if len(df) > 0 else "N/A"
                summary += f"    - {col}: {sample_val}\n"
        
        if text_cols:
            summary += f"  Text columns: {', '.join(text_cols[:3])}\n"
        
        summary_parts.append(summary)
    
    return "\n".join(summary_parts)


def generate_answer_with_llm(question, reasoned_data, chart_path, tables):
    """Generate LLM answer for successful calculations"""
    
    try:
        # Get additional context from RAG
        rag_contexts = retrieve_context(question, k=3)
        rag_text = build_rag_context(rag_contexts)
        
        # Format computed result
        result_text = f"""
**Calculation Result:**
- Value: {reasoned_data.get('result')}
- Confidence: {reasoned_data.get('confidence', 0):.0%}
- Reasoning: {reasoned_data.get('reasoning', 'N/A')}

**Calculation Steps:**
{chr(10).join(reasoned_data.get('reasoning_log', []))}
"""
        
        narrator = LLMNarrator()
        return narrator.explain(
            user_question=question,
            rag_context=rag_text,
            computed_result=result_text,
            charts=[chart_path] if chart_path else None
        )
    
    except Exception as e:
        print(f"❌ LLM answer generation failed: {e}")
        # Fallback to basic formatting
        return format_basic_answer(reasoned_data, chart_path)


def format_basic_answer(reasoned_data, chart_path):
    """Fallback formatting if LLM fails"""
    
    answer = f"""
**Result:** {reasoned_data.get('result')}

{reasoned_data.get('reasoning', '')}

**Confidence:** {reasoned_data.get('confidence', 0):.0%}
"""
    
    if chart_path:
        answer += f"\n\n📊 **Chart:** See visualization"
    
    return answer
