# src/analysis/comparison_engine.py
"""
Part C-4: Multi-Document Comparison Engine

Enables CFO-grade comparison across multiple files/tables:
- "Compare revenue across uploaded files"
- "Which document has higher expenses?"
- "How did cash change between reports?"

IMPORTANT:
- Per-user scope only (no cross-user data)
- Deterministic (no LLM guessing)
- Uses C-3 financial reasoning for each file
- Fully auditable with explanation
"""

from typing import List, Dict, Any, Optional, Tuple
from src.analysis.financial_reasoning import MetricReasoner, COLUMN_SYNONYMS
import pandas as pd

# =============================================================================
# COMPARISON INTENT DETECTION
# =============================================================================

COMPARISON_KEYWORDS = [
    "compare", "comparison", "vs", "versus", "between",
    "difference", "diff", "change", "across",
    "which is higher", "which is lower", "which has more",
    "trend across", "all files", "all documents"
]

def is_comparison_query(query: str) -> bool:
    """
    Detect if query requires comparison across multiple sources.
    """
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in COMPARISON_KEYWORDS)

def extract_metric_from_query(query: str) -> Optional[str]:
    """
    Extract which metric the user wants to compare.
    
    Returns:
        "burn_rate", "revenue_growth", "gross_margin", etc.
    """
    query_lower = query.lower()
    
    # Map of query patterns to metric names
    metric_patterns = {
        "burn_rate": ["burn rate", "burn", "runway", "cash burn"],
        "revenue_growth": ["revenue growth", "revenue", "sales growth", "sales"],
        "gross_margin": ["gross margin", "gross profit margin"],
        "net_profit_margin": ["net profit margin", "profit margin", "net margin"],
        "cash": ["cash", "cash balance", "cash position"],
        "expenses": ["expenses", "operating expenses", "costs"],
    }
    
    for metric, patterns in metric_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            return metric
    
    return None

# =============================================================================
# MULTI-TABLE METRIC COLLECTOR
# =============================================================================

class MultiTableComparator:
    """
    Collects and compares metrics across multiple tables/files.
    
    Uses C-3 (financial_reasoning) for each table individually,
    then aggregates results deterministically.
    """
    
    def __init__(self, tables: List[dict]):
        """
        Args:
            tables: List of cleaned table dicts with structure:
                    {"df": DataFrame, "source": filename, "table_id": int}
        """
        self.tables = tables
        self.comparison_log = []
    
    def _log(self, message: str):
        """Track comparison reasoning for auditability"""
        self.comparison_log.append(message)
    
    def compare_metric(self, metric_name: str) -> Dict[str, Any]:
        """
        Compare a specific metric across all tables.
        
        Args:
            metric_name: "burn_rate", "revenue_growth", etc.
        
        Returns:
            {
                "success": bool,
                "metric": str,
                "results": [{"source": str, "value": float, "reasoning": str}, ...],
                "ranking": [highest to lowest],
                "summary": str,
                "confidence": float
            }
        """
        self._log(f"Starting comparison for metric: {metric_name}")
        
        # Collect results from each table
        results = []
        
        # Group tables by source file
        tables_by_source = {}
        for table in self.tables:
            source = table.get("source", "unknown")
            if source not in tables_by_source:
                tables_by_source[source] = []
            tables_by_source[source].append(table)
        
        self._log(f"Found {len(tables_by_source)} unique source files")
        
        # Run metric reasoning on each source
        for source, source_tables in tables_by_source.items():
            self._log(f"Analyzing {source}...")
            
            reasoner = MetricReasoner(source_tables)
            
            # Call appropriate metric function
            if metric_name == "burn_rate":
                result = reasoner.compute_burn_rate()
            elif metric_name == "revenue_growth":
                result = reasoner.compute_revenue_growth()
            elif metric_name == "gross_margin":
                result = reasoner.compute_gross_margin()
            else:
                # For simple value extraction (cash, revenue, etc.)
                result = self._extract_simple_metric(source_tables, metric_name)
            
            if result.get("success"):
                results.append({
                    "source": source,
                    "value": result.get("result"),
                    "reasoning": result.get("reasoning", ""),
                    "calculation": result.get("calculation", ""),
                    "confidence": result.get("confidence", 0.0),
                    "variables": result.get("variables", {})
                })
                self._log(f"  ✅ {source}: {result.get('result')}")
            else:
                self._log(f"  ⚠️ {source}: {result.get('reasoning', 'Failed')}")
        
        # Check if we got enough results
        if len(results) < 2:
            return {
                "success": False,
                "metric": metric_name,
                "results": results,
                "summary": f"Cannot compare {metric_name}: Need at least 2 files with this metric. Found {len(results)}.",
                "confidence": 0.3
            }
        
        # Rank results
        ranking = sorted(results, key=lambda x: x["value"], reverse=True)
        
        # Generate summary
        summary = self._generate_comparison_summary(metric_name, ranking)
        
        # Calculate overall confidence
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        
        return {
            "success": True,
            "metric": metric_name,
            "results": results,
            "ranking": ranking,
            "summary": summary,
            "confidence": avg_confidence,
            "comparison_log": self.comparison_log
        }
    
    def _extract_simple_metric(self, tables: List[dict], metric_name: str) -> Dict[str, Any]:
        """
        Extract simple metrics like 'cash', 'revenue' that don't need complex calculation.
        """
        # Get column synonyms for this metric
        synonyms = COLUMN_SYNONYMS.get(metric_name, [metric_name])
        
        for table in tables:
            df = table.get("df")
            if df is None or df.empty:
                continue
            
            # Try to find matching column
            for col in df.columns:
                col_lower = str(col).lower()
                
                for synonym in synonyms:
                    if synonym in col_lower:
                        # Extract latest value
                        try:
                            series = pd.to_numeric(df[col], errors='coerce').dropna()
                            if not series.empty:
                                value = float(series.iloc[-1])
                                
                                return {
                                    "success": True,
                                    "result": value,
                                    "reasoning": f"Found {metric_name} as '{col}' with value ${value:,.0f}",
                                    "confidence": 0.9
                                }
                        except:
                            continue
        
        return {
            "success": False,
            "reasoning": f"Could not find {metric_name} in any table",
            "confidence": 0.0
        }
    
    def _generate_comparison_summary(self, metric_name: str, ranking: List[Dict]) -> str:
        """
        Generate human-readable comparison summary.
        """
        if not ranking:
            return f"No data available for {metric_name}"
        
        highest = ranking[0]
        lowest = ranking[-1]
        
        # Format metric name nicely
        metric_display = metric_name.replace("_", " ").title()
        
        summary_parts = [f"{metric_display} Comparison:\n"]
        
        # List all results
        for i, item in enumerate(ranking, 1):
            value = item["value"]
            source = item["source"]
            
            # Format value based on metric type
            if "margin" in metric_name or "growth" in metric_name:
                value_str = f"{value:+.1f}%"
            elif "rate" in metric_name:
                value_str = f"{value:.1f} months"
            else:
                value_str = f"${value:,.0f}"
            
            summary_parts.append(f"{i}. {source}: {value_str}")
        
        # Add conclusion
        if len(ranking) > 1:
            diff = highest["value"] - lowest["value"]
            
            if "margin" in metric_name or "growth" in metric_name:
                diff_str = f"{abs(diff):.1f} percentage points"
            elif "rate" in metric_name:
                diff_str = f"{abs(diff):.1f} months"
            else:
                diff_str = f"${abs(diff):,.0f}"
            
            summary_parts.append(f"\n📊 Highest: {highest['source']}")
            summary_parts.append(f"📊 Lowest: {lowest['source']}")
            summary_parts.append(f"📊 Difference: {diff_str}")
        
        return "\n".join(summary_parts)

# =============================================================================
# SIMPLE INTERFACE
# =============================================================================

def compare_across_documents(
    query: str,
    tables: List[dict]
) -> Dict[str, Any]:
    """
    Main entry point for document comparison.
    
    Args:
        query: User's comparison question
        tables: List of all cleaned tables (per-user scope)
    
    Returns:
        Comparison result with rankings and explanations
    """
    
    # Check if this is actually a comparison query
    if not is_comparison_query(query):
        return {
            "success": False,
            "summary": "This doesn't appear to be a comparison question. Try asking 'compare X across files' or 'which file has higher Y'.",
            "is_comparison": False
        }
    
    # Extract metric to compare
    metric = extract_metric_from_query(query)
    
    if not metric:
        return {
            "success": False,
            "summary": "I understand you want to compare, but couldn't identify which metric. Try: 'compare revenue', 'compare burn rate', etc.",
            "is_comparison": True,
            "metric": None
        }
    
    # Run comparison
    comparator = MultiTableComparator(tables)
    result = comparator.compare_metric(metric)
    
    return result

# =============================================================================
# CHART SELECTION FOR COMPARISON
# =============================================================================

def select_comparison_charts(
    comparison_result: Dict[str, Any],
    available_charts: List[str]
) -> List[str]:
    """
    Select most relevant existing charts for comparison visualization.
    
    Does NOT generate new charts - just picks from already created ones.
    
    Args:
        comparison_result: Result from compare_across_documents()
        available_charts: List of chart file paths already generated
    
    Returns:
        List of relevant chart paths
    """
    if not comparison_result.get("success"):
        return []
    
    metric = comparison_result.get("metric", "")
    sources = [r["source"] for r in comparison_result.get("results", [])]
    
    relevant_charts = []
    
    for chart_path in available_charts:
        chart_path_lower = chart_path.lower()
        
        # Check if chart matches metric and source
        metric_match = any(m in chart_path_lower for m in [metric, metric.replace("_", "")])
        source_match = any(src.replace(".", "_") in chart_path_lower for src in sources)
        
        if metric_match and source_match:
            relevant_charts.append(chart_path)
    
    return relevant_charts[:5]  # Max 5 charts per comparison

# =============================================================================
# TESTING FUNCTION
# =============================================================================

def test_comparison():
    """Test comparison engine with sample data"""
    print("🧪 Testing Comparison Engine...")
    
    # Sample tables
    sample_tables = [
        {
            "df": pd.DataFrame({
                "revenue": [100000, 120000, 150000],
                "expenses": [60000, 70000, 80000]
            }),
            "source": "file_a.pdf",
            "table_id": 0
        },
        {
            "df": pd.DataFrame({
                "sales": [80000, 95000, 110000],
                "costs": [50000, 55000, 60000]
            }),
            "source": "file_b.xlsx",
            "table_id": 0
        }
    ]
    
    # Test query
    query = "compare revenue across files"
    
    result = compare_across_documents(query, sample_tables)
    
    print(f"\n✅ Result:")
    print(f"Success: {result.get('success')}")
    print(f"\n{result.get('summary', '')}")
    
    return result

if __name__ == "__main__":
    test_comparison()
