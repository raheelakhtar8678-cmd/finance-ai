# src/analysis/comparison_engine.py
"""
Multi-Document Comparison Engine
Enables comparison of financial figures across different uploaded files (PDF, CSV, XLSX).
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from src.analysis.financial_reasoning import compute_metric_with_reasoning
from src.analysis.metric_registry import METRIC_REGISTRY

# Keywords that trigger comparison across different documents
MULTI_DOC_TRIGGERS = [
    "across", "all files", "all documents", "multi-file", 
    "cross check", "check across", "both documents", "all three"
]

# Simple comparison words (might be used for triangulation within one doc)
SIMPLE_COMP_KEYWORDS = [
    "compare", "comparison", "vs", "versus", "between",
    "difference", "diff", "change"
]

def is_comparison_query(query: str) -> bool:
    """
    Detect if query requires comparison ACROSS multiple sources.
    
    NOTE: This function now focuses ONLY on cross-document comparisons.
    Temporal comparisons (YoY, QoQ, etc.) are handled by temporal_comparison.py
    """
    from src.analysis.temporal_comparison import is_temporal_comparison
    
    q = query.lower()
    
    # 🔑 NEW: Delegate temporal comparisons to temporal engine
    if is_temporal_comparison(query):
        print("🕐 [COMPARE] Detected temporal comparison - delegating to temporal engine")
        return False  # Not a cross-document comparison
    
    # If it has a hard trigger, it's definitely cross-document
    if any(tk in q for tk in MULTI_DOC_TRIGGERS):
        return True
    
    # If it has a simple keyword, check if it mentions multiple metrics
    if any(sk in q for sk in SIMPLE_COMP_KEYWORDS):
        # Count how many distinct metrics are mentioned
        from src.analysis.metric_registry import METRIC_REGISTRY
        metrics_found = set()
        for m, config in METRIC_REGISTRY.items():
            if any(kw in q for kw in config["keywords"]):
                metrics_found.add(m)
        
        # If comparing DIFFERENT metrics (e.g. profit vs revenue), skip Layer 0 
        # Layer 0 is for comparing the SAME metric ACROSS files.
        if len(metrics_found) > 1:
            print(f"⚖️ Multi-metric query detected ({metrics_found}). Routing to RAG/Reasoning for reconciliation.")
            return False
            
        return True
        
    return False

def extract_metric_from_query(query: str) -> Optional[str]:
    """Identify which metric the user wants to compare using METRIC_REGISTRY.
    Prioritizes longer keyword matches to avoid 'income' vs 'net income' overlap.
    """
    query_lower = query.lower()
    
    matches = []
    for metric, config in METRIC_REGISTRY.items():
        for kw in config["keywords"]:
            if kw in query_lower:
                matches.append((metric, len(kw)))
    
    if matches:
        # Sort by match length descending
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]
        
    return None

class MultiTableComparator:
    """
    Orchestrates comparison of metrics across multiple source documents.
    """
    
    def __init__(self, tables: List[dict]):
        self.tables = tables
        self.comparison_log = []
    
    def _log(self, message: str):
        self.comparison_log.append(message)
        print(f"📊 [COMPARE] {message}")
    
    def compare_metric(self, metric_name: str, question: str) -> Dict[str, Any]:
        """
        Runs reasoning for the specified metric on each document separately.
        """
        self._log(f"Starting cross-document comparison for: {metric_name}")
        
        # Group tables by source file
        tables_by_source = {}
        for table in self.tables:
            source = table.get("source", "unknown")
            if source not in tables_by_source:
                tables_by_source[source] = []
            tables_by_source[source].append(table)
        
        if len(tables_by_source) < 2:
            return {
                "success": False,
                "summary": f"Comparison requires at least two different documents. Only found: {list(tables_by_source.keys())}",
                "confidence": 0.3
            }

        results = []
        for source, source_tables in tables_by_source.items():
            self._log(f"Analyzing source: {source}")
            
            # Use the unified reasoning entry point
            res = compute_metric_with_reasoning(metric_name, source_tables, question)
            
            if res.get("success"):
                results.append({
                    "source": source,
                    "value": res.get("result"),
                    "period": res.get("period_date", "unknown"),
                    "reasoning": res.get("reasoning", ""),
                    "confidence": res.get("confidence", 0.0)
                })
                self._log(f"  ✅ {source}: {res.get('result')} ({res.get('period_date')})")
            else:
                self._log(f"  ❌ {source}: Could not extract metric.")

        if len(results) < 2:
            return {
                "success": False,
                "summary": f"Could only extract '{metric_name}' from one document. Found in: {[r['source'] for r in results]}",
                "confidence": 0.4
            }

        # Sort results (highest value first)
        results.sort(key=lambda x: x["value"] if isinstance(x["value"], (int, float)) else 0, reverse=True)
        
        summary = self._generate_summary(metric_name, results)
        
        return {
            "success": True,
            "metric": metric_name,
            "results": results,
            "summary": summary,
            "confidence": sum(r["confidence"] for r in results) / len(results)
        }

    def _generate_summary(self, metric: str, results: List[Dict]) -> str:
        """Builds a human-readable comparison table with correct units."""
        lines = [f"Comparison of {metric.replace('_', ' ').title()} across documents:\n"]
        
        # Determine unit type
        metric_config = METRIC_REGISTRY.get(metric, {})
        unit_type = metric_config.get("unit", "currency")
        
        for i, r in enumerate(results, 1):
            val = r['value']
            # Format value
            if isinstance(val, (int, float)):
                if unit_type == "percent":
                    f_val = f"{val:.2f}%"
                elif unit_type == "ratio":
                    f_val = f"{val:.2f}x"
                else: 
                    # Default: Currency
                    if val >= 1_000_000_000: f_val = f"${val/1_000_000_000:.2f}B"
                    elif val >= 1_000_000: f_val = f"${val/1_000_000:.2f}M"
                    else: f_val = f"${val:,.2f}"
            else:
                f_val = str(val)
                
            lines.append(f"{i}. **{r['source']}**: {f_val} (Period: {r['period']})")
        
        if len(results) >= 2:
            v1 = results[0]['value']
            v2 = results[-1]['value']
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                diff = v1 - v2
                
                if unit_type == "percent":
                    lines.append(f"\n**Difference (High vs Low)**: {diff:.2f} percentage points")
                elif unit_type == "ratio":
                    lines.append(f"\n**Difference (High vs Low)**: {diff:.2f}x")
                else:
                    lines.append(f"\n**Difference (High vs Low)**: ${diff:,.2f}")
                
        # 🎯 NEW: CFO Insights Injection
        cfo_block = ""
        try:
            from src.analysis.cfo_insights import CFOInsights
            from dateutil import parser
            
            # Try to sort results by period date to find Current vs Prior
            # (The default sort above was by Value, which is good for ranking but bad for variance)
            sorted_by_date = []
            for r in results:
                p_str = str(r.get("period", ""))
                try:
                    dt = parser.parse(p_str, fuzzy=True)
                    sorted_by_date.append((dt, r))
                except:
                    # Fallback: maintain original order if date parse fails
                    pass
            
            # If we successfully parsed dates for at least 2 items
            if len(sorted_by_date) >= 2:
                # Sort descending (Latest first)
                sorted_by_date.sort(key=lambda x: x[0], reverse=True)
                
                current = sorted_by_date[0][1]
                prior = sorted_by_date[1][1]
                
                cfo = CFOInsights()
                cfo_block = cfo.generate_cfo_commentary(
                    metric_name=metric,
                    segment="Cross-Document",
                    current_val=current['value'],
                    prior_val=prior['value'],
                    period_label=current['period']
                )
                if cfo_block:
                    cfo_block = f"\n\n### 💼 CFO STRATEGIC ADVISORY\n{cfo_block}"
                    
        except ImportError:
            pass # dateutil not installed or other error
        except Exception as e:
            print(f"⚠️ CFO Cross-Doc Logic failed: {e}")

        return "\n".join(lines) + cfo_block

def compare_across_documents(query: str, tables: List[dict]) -> Dict[str, Any]:
    """Entry point for multi-document comparison."""
    if not is_comparison_query(query):
        return {"success": False, "is_comparison": False}
        
    metric = extract_metric_from_query(query)
    if not metric:
        return {
            "success": False, 
            "summary": "Detected comparison intent, but couldn't identify the metric (revenue, profit, etc.).",
            "is_comparison": True
        }
        
    comparator = MultiTableComparator(tables)
    return comparator.compare_metric(metric, query)
