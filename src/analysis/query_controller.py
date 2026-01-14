# src/analysis/query_controller.py
"""
Flexible Query Controller
Deterministic Metrics → RAG → LLM (with charts)
"""

import pandas as pd
from pathlib import Path

from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.analysis.question_router import resolve_intent, detect_segment_filter
from src.ai.rag_engine import retrieve_context
from src.ai.llm_narrator import LLMNarrator
from src.visualization.chart_generator import generate_chart
from src.analysis.comparison_engine import compare_across_documents, is_comparison_query
from src.analysis.metric_registry import METRIC_REGISTRY

# Ensure pandas doesn't truncate/wrap tables in summaries
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.expand_frame_repr', False)  # 👈 Prevents wrapping wide tables


# ======================================================
# MAIN ENTRY
# ======================================================
def route_query(question, tables, chart_gen=None, session_id=None):
    """
    Universal query router.
    ALWAYS generates chart if numeric trend exists.
    """
    cleaned_tables = tables
    from src.ai.llm_narrator import LLMNarrator
    narrator = LLMNarrator()
    print(f"\n🔍 Processing question: {question}")

    # 🔑 PERFORMANCE: Check cache first
    try:
        from src.cache.response_cache import cached_query, cache_response
        cached = cached_query(question, session_id or "default")
        if cached:
            print(f"⚡ [CACHE] Returning cached response")
            return cached  # Returns (answer, chart_path) tuple
    except ImportError:
        pass  # Cache module not available, continue without caching
    except Exception as e:
        print(f"⚠️ [CACHE] Error: {e}")

    # 🔑 NEW: Extract source files for session-based RAG isolation
    source_files = list(set(t.get("source", "") for t in tables if t.get("source")))
    if source_files:
        print(f"📂 [SESSION] Source files: {source_files}")

    # --------------------------------------------------
    # LAYER 0 – MULTI-DOCUMENT COMPARISON
    # --------------------------------------------------
    
    if is_comparison_query(question):
        print("🔗 [CONTROLLER] Detected cross-document comparison intent.")
        comp_res = compare_across_documents(question, cleaned_tables)
        
        if comp_res.get("success"):
            
            # Generate a comparison chart for the different files
            comp_chart = None
            if chart_gen:
                results = comp_res.get("results", [])
                df_comp = pd.DataFrame({
                    "Source": [r["source"] for r in results],
                    "Value": [r["value"] for r in results]
                })
                m_name = comp_res.get("metric", "Comparison")
                chart_out = chart_gen(
                    df=df_comp,
                    x_col="Source",
                    y_col="Value",
                    title=f"Cross-Document {m_name.title()} Comparison",
                    output_path=f"data/static/multi_doc_comp.png",
                    chart_type="bar"
                )
                if chart_out.get("success"):
                    comp_chart = chart_out["image_path"]

            answer = narrator.explain(
                user_question=question,
                rag_context="This is a deterministic multi-document comparison.",
                computed_result=comp_res.get("summary"),
                charts=[comp_chart] if comp_chart else None
            )
            return answer, comp_chart

    # --------------------------------------------------
    # LAYER 0.5 – TEMPORAL COMPARISON (YoY, QoQ, etc.)
    # --------------------------------------------------
    from src.analysis.temporal_comparison import is_temporal_comparison, handle_temporal_comparison
    
    if is_temporal_comparison(question):
        print("🕐 [CONTROLLER] Detected temporal comparison intent.")
        temporal_res = handle_temporal_comparison(question, cleaned_tables)
        
        if temporal_res.get("success"):
            # Generate temporal comparison chart
            temp_chart = None
            if chart_gen and temporal_res.get("chart_data") is not None:
                df_temp = temporal_res["chart_data"]
                m_name = temporal_res.get("metric", "Metric")
                segment = temporal_res.get("segment", "")
                
                title = f"{m_name.replace('_', ' ').title()}"
                if segment:
                    title += f" - {segment}"
                title += " (Temporal Comparison)"
                
                chart_out = chart_gen(
                    df=df_temp,
                    x_col="Period",
                    y_col="Value",
                    title=title,
                    output_path=f"data/static/temporal_comp.png",
                    chart_type="bar"
                )
                if chart_out.get("success"):
                    temp_chart = chart_out["image_path"]
            
            answer = narrator.explain(
                user_question=question,
                rag_context="This is a deterministic temporal comparison across periods.",
                computed_result=temporal_res.get("summary"),
                charts=[temp_chart] if temp_chart else None
            )
            return answer, temp_chart
        else:
            # Temporal comparison failed, fall through to RAG
            print(f"⚠️ [TEMPORAL] Failed: {temporal_res.get('error', 'Unknown error')}")
            print("   Falling back to RAG + LLM")

    # --------------------------------------------------
    # LAYER 1.5 – FORMULA-BASED CALCULATIONS
    # --------------------------------------------------
    # Detect if user is asking for a financial ratio/formula
    from src.analysis.financial_formulas import (
        detect_formula_query, calculate_formula, FORMULA_REGISTRY, format_result
    )
    
    formula_name = detect_formula_query(question)
    if formula_name:
        print(f"📐 [CONTROLLER] Detected formula query: {formula_name}")
        
        # Try to extract required inputs from tables
        from src.analysis.financial_formulas import get_required_inputs
        required_inputs = get_required_inputs(formula_name)
        
        # Build data dict from extracted metrics
        extracted_data = {}
        for req_input in required_inputs:
            # Try to find this input in tables using metric extraction
            matched = resolve_intent(req_input)
            if matched:
                for m_name, m_config in matched:
                    res = compute_metric_with_reasoning(m_name, cleaned_tables, req_input)
                    if res.get("success") and res.get("result") is not None:
                        extracted_data[req_input] = res["result"]
                        print(f"   ✅ Extracted {req_input}: {res['result']}")
                        break
        
        # Try to calculate the formula
        if extracted_data:
            calc_result = calculate_formula(formula_name, extracted_data)
            
            if calc_result.get('success'):
                formula_summary = f"""
## 📐 Calculated Formula: {calc_result['formula_name']}

**Formula:** {calc_result['formula_text']}

**Result:** {format_result(calc_result).strip()}

### Inputs Used
| Input | Value |
|-------|-------|
""" + "\n".join(f"| {k} | {v:,.2f} |" for k, v in calc_result['inputs_used'].items())
                
                answer = narrator.explain(
                    user_question=question,
                    rag_context="Formula calculated from extracted financial data.",
                    computed_result=formula_summary,
                    charts=None
                )
                return answer, None
            else:
                print(f"   ⚠️ Formula calculation failed: {calc_result.get('error')}")
        else:
            print(f"   ⚠️ Could not extract required inputs for formula: {required_inputs}")

    # --------------------------------------------------
    # LAYER 2 – DETERMINISTIC METRICS
    # --------------------------------------------------
    # resolve_intent now returns a list of (metric_name, metric_config)
    matched_metrics = resolve_intent(question)

    if matched_metrics:
        # Detect segment filter (e.g., "Greater China", "iPhone")
        segment_filter = detect_segment_filter(question)
        if segment_filter:
            print(f"🎯 Segment Filter Detected: '{segment_filter}'")

        # Collect results for all identified metrics
        results = []
        for m_name, m_config in matched_metrics:
            res = compute_metric_with_reasoning(m_name, cleaned_tables, question, segment_filter=segment_filter)
            if res.get("success"):
                results.append((m_name, res))

        if results:
            if len(results) == 1:
                # Single-metric flow (Backward Compatibility)
                m_name, result = results[0]
                print(f"🎯 Single metric success: {m_name}")
                current_val = result.get("result")
                prior_val = result.get("prior_result")
                chart_path = result.get("chart_path")

                if not chart_path and current_val is not None and chart_gen:
                    try:
                        config = METRIC_REGISTRY.get(m_name, {})
                        df_chart = pd.DataFrame({"Period": [result.get("prior_date", "Prior"), result.get("period_date", "Current")], "Value": [prior_val, current_val]})
                        chart_res = chart_gen(df=df_chart, x_col="Period", y_col="Value", title=f"{m_name.replace('_', ' ').title()} Analysis", output_path=f"data/static/{m_name}_proof.png", chart_type=config.get("chart", "bar"))
                        if chart_res.get("success"): chart_path = chart_res["image_path"]
                    except: pass

                return generate_metric_answer(question, result, chart_path, metric_name=m_name), chart_path
            
            else:
                # ⚖️ MULTI-METRIC RECONCILIATION FLOW (Triangulation)
                print(f"⚖️ Reconciling {len(results)} metrics Deterministically.")
                combined_verified = []
                for m_name, res in results:
                    if res.get("result") is not None:
                        val = format_currency(res.get("result"), metric_name=m_name)
                        curr_part = f"{m_name.replace('_',' ').title()}: {val} (As of {res.get('period_date')})"
                        
                        prior_val = res.get("prior")
                        if prior_val:
                            p_val = format_currency(prior_val, metric_name=m_name)
                            curr_part += f" | Prior: {p_val} (As of {res.get('prior_date', 'prior')})"
                        
                        combined_verified.append(f"- {curr_part}")
                
                verified_text = "\n".join(combined_verified)
                
                # Still use RAG for supplemental context (footnotes)
                rag_contexts = retrieve_context(question, k=10, source_filter=source_files if source_files else None)
                rag_text = build_rag_context(rag_contexts)
                table_summary = build_table_summary(cleaned_tables, question=question)

                answer = narrator.explain(
                    user_question=question,
                    rag_context=f"{table_summary}\n\n{rag_text}",
                    computed_result=f"Verified Figures:\n{verified_text}\n\nReasoning: Multiple metrics extracted deterministically for reconciliation.",
                    charts=None
                )
                return answer, None

    # --------------------------------------------------
    # LAYER 2 – RAG + LLM (Fallback)
    # --------------------------------------------------
    print("🔍 Falling back to RAG + smart chart")

    rag_contexts = retrieve_context(question, k=10, source_filter=source_files if source_files else None)
    rag_text = build_rag_context(rag_contexts)
    
    # Pass question for smart table filtering
    table_summary = build_table_summary(cleaned_tables, question=question)

    # 💇 THIS IS THE IMPORTANT PART
    chart_path = try_smart_chart(
        question=question,
        tables=cleaned_tables,
        chart_gen=chart_gen
    )

    narrator = LLMNarrator()

    answer = narrator.explain(
        user_question=question,
        rag_context=rag_text,
        computed_result=table_summary,
        charts=[chart_path] if chart_path else None
    )

    return answer, chart_path


# ======================================================
# METRIC ANSWER
# ======================================================
def generate_metric_answer(question, metric_result, chart_path=None, metric_name=None):
    """
    🎯 PRODUCT-GRADE: Generate natural language answer from metric computation.
    
    The LLM receives a pre-computed "fact sheet" - its job is to EXPLAIN, not FIND.
    """
    narrator = LLMNarrator()

    rag_contexts = retrieve_context(question, k=3)
    rag_text = build_rag_context(rag_contexts)

    # ✅ INJECT THE SOURCE TABLE INTO CONTEXT
    # This fixes the "Discrepancy" where LLM says it can't find the number in text.
    if metric_result.get("context_table_str"):
        rag_text = f"*** PRIMARY SOURCE TABLE (Period: {metric_result.get('period_date')}) ***\n{metric_result.get('context_table_str')}\n\n" + rag_text

    # Format the result
    result_value = metric_result.get('result')
    prior_value = metric_result.get('prior')
    
    formatted_value = format_currency(result_value, metric_name=metric_name)
    formatted_prior = format_currency(prior_value, metric_name=metric_name) if prior_value else None

    # --- EXTRA CONTEXT ---
    extra_facts = []
    if metric_result.get('operating_income'):
        val = format_currency(metric_result.get('operating_income'))
        p_val = format_currency(metric_result.get('operating_income_prior'))
        extra_facts.append(f"  - Operating Income: {val} (Prior: {p_val or 'N/A'})")
    
    if metric_result.get('revenue'):
        val = format_currency(metric_result.get('revenue'))
        p_val = format_currency(metric_result.get('revenue_prior'))
        extra_facts.append(f"  - Total Net Sales: {val} (Prior: {p_val or 'N/A'})")

    if metric_result.get('eps'):
        val = f"${metric_result.get('eps'):.2f}"
        p_val = f"${metric_result.get('eps_prior'):.2f}" if metric_result.get('eps_prior') else "N/A"
        extra_facts.append(f"  - Earnings Per Share (EPS): {val} (Prior: {p_val})")

    extra_text = "\n".join(extra_facts) + "\n" if extra_facts else ""
    
    # 🎯 PRODUCT-GRADE: Fact Sheet Format
    # This makes the LLM's job trivial - it just needs to explain, not find
    metric_display = (metric_name or "Metric").replace("_", " ").title()
    confidence_pct = metric_result.get('confidence', 0) * 100
    
    # 🎯 NEW: CFO Insights Injection
    cfo_section = ""
    try:
        from src.analysis.cfo_insights import CFOInsights
        cfo = CFOInsights()
        if result_value is not None and prior_value is not None:
             # Basic segment validation
            segment_lbl = "Company"
            if "segment" in str(metric_result.get("reasoning", "")).lower():
                # Try to clean up segment name from reasoning or context
                pass
            
            cfo_text = cfo.generate_cfo_commentary(
                metric_name=metric_name or "Metric",
                segment=segment_lbl,
                current_val=result_value,
                prior_val=prior_value,
                period_label=metric_result.get('period_date', 'Current')
            )
            if cfo_text:
                cfo_section = f"\n### 💼 CFO STRATEGIC ADVISORY\n{cfo_text}\n"
    except Exception as e:
        print(f"⚠️ CFO Insights failed: {e}")

    result_text = f"""
## 📊 FACT SHEET: {metric_display}

### ANSWER (Pre-Computed)
**{formatted_value}**

### DETAILS
| Field | Value |
|-------|-------|
| Current Period | {metric_result.get('period_date', 'Current')} |
| Current Value | {formatted_value} |
| Prior Period | {metric_result.get('prior_date', 'Prior')} |
| Prior Value | {formatted_prior or 'N/A'} |
| Confidence | {confidence_pct:.0f}% |

### SOURCE ATTRIBUTION
- **Extraction Method**: {metric_result.get('source', 'Deterministic')}
- **Reasoning**: {metric_result.get('reasoning', 'Direct table lookup')}

{f"### ADDITIONAL METRICS{chr(10)}{extra_text}" if extra_facts else ""}
{cfo_section}
---
**YOUR TASK**: Explain this computed result to the user in clear, analyst-quality language. 
Do NOT search for the number - it has already been verified above.
If the 'CFO STRATEGIC ADVISORY' section is present, YOU MUST INCLUDE its recommendations in your final response.
"""

    return narrator.explain(
        user_question=question,
        rag_context=rag_text,
        computed_result=result_text,
        charts=[chart_path] if chart_path else None
    )

def format_currency(value, metric_name=None):
    if value is None: return None
    if not isinstance(value, (int, float)): return str(value)
    
    # Check unit type from registry
    unit_type = "currency"
    if metric_name:
        from src.analysis.metric_registry import METRIC_REGISTRY
        config = METRIC_REGISTRY.get(metric_name, {})
        unit_type = config.get("unit", "currency")

    # Format based on unit
    if unit_type == "percent":
        return f"{value:.2f}%"
    elif unit_type == "ratio":
        return f"{value:.2f}x"
    
    # Default: Currency
    if abs(value) >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f} billion"
    elif abs(value) >= 1_000_000:
        return f"${value/1_000_000:.2f} million"
    else:
        return f"${value:,.2f}"


# ======================================================
# SMART CHART (RAG FALLBACK)
# ======================================================
def try_smart_chart(question, tables, chart_gen=None):
    """
    Try to generate a relevant chart based on the question.
    Elite RAG: Handles product and geographic breakdowns with best-match scoring.
    """
    if not chart_gen or not tables:
        return None

    q = question.lower()
    Path("data/static").mkdir(parents=True, exist_ok=True)

    def is_numeric_ish(series):
        """Check if series is numeric or contains string numbers with commas/currency."""
        if pd.api.types.is_numeric_dtype(series): return True
        sample = series.dropna().head(5).astype(str)
        if sample.empty: return False
        clean_sample = sample.str.replace(r'[$,% ]', '', regex=True).replace(',', '', regex=True)
        try:
            pd.to_numeric(clean_sample)
            return True
        except:
            return False

    potential_charts = []

    # 1. SPECIAL CASE: "Breakdown" / "Product" / "Region" -> BAR CHART
    breakdown_keywords = ["product", "breakdown", "segment", "mix", "source", "country", "geography", "region", "category"]
    
    for table in tables:
        df = table["df"]
        if len(df.columns) < 2 or len(df) < 2: continue
        
        col0, col1 = df.columns[0], df.columns[1]
        if pd.api.types.is_object_dtype(df[col0]) and is_numeric_ish(df[col1]) and 2 <= len(df) <= 18:
            # Score this table's relevance to the breakdown query
            score = 0
            table_text = " ".join([str(c) for c in df.columns] + [str(x) for x in df.head(3).values.flatten()]).lower()
            
            # Semantic overlap boost
            for k in breakdown_keywords + question.lower().split():
                if k in table_text: score += 10
            
            potential_charts.append({
                "score": score,
                "type": "bar",
                "df": df,
                "x": col0, "y": col1,
                "title": f"Breakdown by {col0}"
            })

    # 2. DEFAULT: Keyword Trend Search (Time Series)
    keywords = {
        "revenue": ["revenue", "sales", "turnover", "net sales"],
        "profit": ["profit", "net income", "earnings", "income", "loss"],
        "growth": ["growth", "increase", "trend"],
        "expense": ["expense", "cost", "spending", "operating expenses"],
        "cash": ["cash", "cash flow", "operating activities"]
    }
    
    # 🔑 NEW: Special chart for profit/loss queries from Income Statement
    if any(k in q for k in ["profit", "loss", "income", "earnings", "making"]):
        for table in tables:
            df = table["df"]
            if len(df.columns) < 2 or len(df) < 3: continue
            
            # Check if this looks like an Income Statement
            first_col = " ".join(df.iloc[:, 0].astype(str).tolist()).lower()
            if "net income" in first_col or "net sales" in first_col:
                # Found Income Statement - create bar chart
                col0 = df.columns[0]
                # Use the first numeric column (likely most recent period)
                for col_idx in range(1, min(3, len(df.columns))):
                    col1 = df.columns[col_idx]
                    if is_numeric_ish(df[col1]):
                        potential_charts.append({
                            "score": 100,  # Very high priority
                            "type": "bar",
                            "df": df.head(10),  # Key income statement lines
                            "x": col0, "y": col1,
                            "title": f"Income Statement ({col1})"
                        })
                        break
    
    if not potential_charts:
        for table in tables:
            df = table["df"]
            for concept, words in keywords.items():
                if any(w in q for w in words):
                    for col in df.columns:
                        if any(w in col.lower() for w in words) and is_numeric_ish(df[col]):
                            score = 20 # Constant base for trend
                            table_text = " ".join([str(c) for c in df.columns]).lower()
                            if any(w in table_text for w in words): score += 10
                            
                            potential_charts.append({
                                "score": score,
                                "type": "trend",
                                "df": df,
                                "x": df.columns[0], "y": col,
                                "title": f"{col} Trend"
                            })

    if potential_charts:
        # Sort by score descending and take best
        best = sorted(potential_charts, key=lambda x: x["score"], reverse=True)[0]
        print(f"📊 Selected best potential chart: {best['title']} (Score {best['score']})")
        
        df_chart = best["df"].copy()
        y_col = best["y"]
        if not pd.api.types.is_numeric_dtype(df_chart[y_col]):
            df_chart[y_col] = df_chart[y_col].astype(str).str.replace(r'[$,% ]', '', regex=True).replace(',', '', regex=True)
            df_chart[y_col] = pd.to_numeric(df_chart[y_col], errors='coerce')
        
        result = chart_gen(
            df=df_chart.dropna(subset=[y_col]),
            x_col=best["x"],
            y_col=y_col,
            chart_type="bar" if best["type"] == "bar" else "line",
            title=best["title"],
            output_path=f"data/static/best_breakdown_chart.png"
        )
        return result.get("image_path")

    return None


# ======================================================
# CONTEXT BUILDERS
# ======================================================
def build_rag_context(contexts):
    """Build formatted context from RAG results"""
    if not contexts:
        return "No relevant document context found."

    blocks = []
    for i, ctx in enumerate(contexts[:5], 1):
        # Handle different context formats
        text = ctx.get('text', '')
        source = ctx.get('meta', {}).get('source', 'Unknown')
        
        blocks.append(
            f"[Source {i}: {source}]\n{text}"
        )

    return "\n\n".join(blocks)


def build_table_summary(tables, question=""):
    """
    Build summary of available table data.
    Prioritizes tables that match keywords in the question.
    """
    if not tables:
        return "No tables available."

    summaries = []
    
    # 1. Score tables by relevance
    scored_tables = []
    q_terms = set(question.lower().split()) if question else set()
    
    # Pre-calculate metric match keywords for scoring
    from src.analysis.question_router import resolve_intent
    matched_metrics = resolve_intent(question)
    metric_keywords = []
    if matched_metrics:
        from src.analysis.metric_registry import METRIC_REGISTRY
        for m_name, _ in matched_metrics:
            keywords = METRIC_REGISTRY.get(m_name, {}).get("keywords", [])
            metric_keywords.extend(keywords)

    # Anchor Keywords for Segments & Footnotes (CFO-Grade)
    segment_anchors = [
        "iphone", "mac", "ipad", "services", "wearables", "americas", "europe", "china", "asia pacific",
        "legal", "investigation", "proceedings", "commitment", "obligation", "payable", 
        "fair value", "hedge", "derivative", "measurement", 
        "inventory", "component", "finished goods", "work in process" 
    ]
    q_low = question.lower()
    is_deep_query = any(k in q_low for k in ["product", "segment", "country", "legal", "note", "obligation", "breakdown", "inventory", "hedge", "fair value"])
    
    # 🔑 CRITICAL: Income Statement Query Detection
    # These queries ALL need the Income Statement (Page 4 in typical 10-Q)
    is_income_statement_query = any(k in q_low for k in [
        # Profit/Loss indicators
        "profit", "loss", "profitable", "making money", "earnings", "losing",
        "net income", "bottom line", "profitability", "income statement",
        # Expense indicators  
        "r&d", "research", "development", "expense", "cost", "spending",
        "operating expense", "sg&a", "selling", "general", "administrative",
        # Revenue indicators (also on Income Statement)
        "revenue", "sales", "net sales", "gross margin",
        # EPS
        "eps", "earnings per share", "shares outstanding"
    ])
    
    if is_income_statement_query:
        print(f"📋 [INCOME STATEMENT] Query triggers Income Statement search: {question[:50]}...")
    
    # Period Anchors (Ensures 3-month vs 6-month alignment)
    is_six_month = any(k in q_low for k in ["six months", "6 months", "6-month", "ytd"])
    is_three_month = any(k in q_low for k in ["three months", "3 months", "3-month", "quarterly"])

    for i, table in enumerate(tables):
        df = table.get("df")
        score = 0
        
        # Handle cases where df is None (e.g. PyMuPDF4LLM Markdown tables)
        if df is None:
            # Fallback to scoring based on markdown content only
            table_text = table.get("markdown", "").lower()
            # If no df, we can't check columns, so we skip column-based logic
            # or treat text presence as main signal
        else:
            table_text = " ".join([str(c) for c in df.columns]).lower()
            if len(df) > 0:
                table_text += " " + " ".join([str(x) for x in df.iloc[0:3].values.flatten()]).lower()
            
            # Also check entire first column for key terms
            if len(df.columns) > 0:
                first_col_text = " ".join(df.iloc[:, 0].astype(str).tolist()).lower()
                table_text += " " + first_col_text
            
            if 2 < len(df) < 15:
                cols = df.columns
                if len(cols) >= 2:
                    is_cat = pd.api.types.is_object_dtype(df[cols[0]])
                    if is_cat: score += 4
        
        for term in q_terms:
            if term in table_text: score += 3 
        
        for kw in metric_keywords:
            if kw in table_text: score += 5
        
        if is_six_month and any(k in table_text for k in ["six months", "six-month"]):
            score += 10
        if is_three_month and any(k in table_text for k in ["three months", "three-month"]):
            score += 10

        if is_deep_query:
            for anchor in segment_anchors:
                if anchor in table_text: score += 8

        if df is not None and 2 < len(df) < 15:
            cols = df.columns
            if len(cols) >= 2:
                is_cat = pd.api.types.is_object_dtype(df[cols[0]])
                if is_cat: score += 4

        core_statements = ["statement of operations", "income statement", "balance sheet", "net sales by", "segment performance", "cash flows", "operations"]
        if any(h in table_text for h in core_statements):
            score += 10
        elif "note" in table_text:
            score += 5 
        
        # 🔑 CRITICAL BOOST for Income Statement queries
        # If user asks about anything on Income Statement, MASSIVELY prioritize it
        if is_income_statement_query:
            # Check for key Income Statement indicators
            if "net income" in table_text:
                score += 50  # MASSIVE boost - THE profit number
                print(f"📊 [INCOME BOOST] Found 'net income' in table {i} (page {table.get('page', '?')}), score now {score}")
            if "operating income" in table_text:
                score += 30
                print(f"📊 [INCOME BOOST] Found 'operating income' in table {i}, score now {score}")
            if "research" in table_text or "r&d" in table_text:
                score += 40  # R&D expenses
                print(f"📊 [INCOME BOOST] Found 'R&D' in table {i}, score now {score}")
            if "statement of operations" in table_text or "income statement" in table_text:
                score += 40
            if "cost of sales" in table_text or "gross margin" in table_text:
                score += 20
            if "earnings per share" in table_text or "eps" in table_text:
                score += 25
            if "total net sales" in table_text:
                score += 30  # Main revenue line 

        scored_tables.append((score, i, table))

    scored_tables.sort(key=lambda x: x[0], reverse=True)
    
    # 🔍 DEBUG: Show top scored tables
    print(f"📊 [TABLE SCORES] Top tables for query: {question[:40]}...")
    for score, idx, tbl in scored_tables[:10]:
        print(f"   Table {idx} (Page {tbl.get('page', '?')}): Score={score}")
    
    # 🎯 PRODUCT-GRADE: Only pass TOP 3 most relevant tables with score >= 10
    # This reduces noise and makes LLM's job much easier
    MIN_RELEVANCE_SCORE = 10
    filtered_tables = [(s, i, t) for s, i, t in scored_tables if s >= MIN_RELEVANCE_SCORE]
    top_tables = [t[2] for t in filtered_tables[:3]]
    
    if not top_tables:
        # Fallback: if no table meets threshold, take top 2 anyway
        top_tables = [t[2] for t in scored_tables[:2]]
        print(f"⚠️ No tables met score threshold {MIN_RELEVANCE_SCORE}, using top 2 fallback")

    for i, table in enumerate(top_tables):
        source = table.get("source", "Unknown")
        page = table.get("page", "?")
        
        df = table.get("df")
        if df is None:
            # Markdown table support
            md_content = table.get("markdown", "No content")
            summaries.append(f"### Table {i+1} (Page {page} from {source})\n\n{md_content}\n")
            continue

        df = df.copy()
        
        # 🩹 HEAL Fragmented columns before cleaning
        try:
            from src.analysis.financial_reasoning import heal_fragmented_columns
            df = heal_fragmented_columns(df)
            
            # 🧹 CLEAN & DE-FRAGMENT
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        except Exception as e:
            print(f"⚠️ Error healing table on page {page}: {e}")
        
        # 🛡️ PROTECT DATA: Keep columns that have substantial data (>5% non-empty)
        # Previously we dropped all "column_N" if a real header existed, which destroyed data fragments.
        informative_cols = []
        for col in df.columns:
            # Count non-empty strings
            non_empty = df[col].apply(lambda x: str(x).strip() != "").sum()
            if non_empty / len(df) > 0.05:
                informative_cols.append(col)
        
        if informative_cols:
            df = df[informative_cols]

        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).str.replace(r'[\r\n]+', ' ', regex=True).str.strip()

        # 🎯 PRODUCT-GRADE: Clean, focused formatting for LLM
        s = f"### Source: {source} (Page {page})\n"
        s += f"**Relevance Score**: High\n\n"
        
        # Use markdown table for cleaner LLM consumption
        try:
            md_table = df.head(30).to_markdown(index=False)
            s += f"{md_table}\n"
        except:
            csv_preview = df.head(30).to_csv(index=False)
            s += f"```\n{csv_preview}\n```\n"
        
        summaries.append(s)

    # Add count indicator for LLM context
    header = f"## Financial Data Context ({len(summaries)} most relevant tables)\n\n"
    return header + "\n---\n\n".join(summaries)