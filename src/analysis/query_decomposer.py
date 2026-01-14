# src/analysis/query_decomposer.py
"""
Query Decomposer for Complex Financial Questions

Breaks down complex queries like:
- "What is the March 29 burn rate compared to Q1 average?"
- "Show me YoY revenue growth for the last 3 quarters"
- "Calculate profit margin trend"

Into atomic, executable steps.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.analysis.date_normalizer import FinancialDateNormalizer, NormalizedDate


class StepType(Enum):
    """Types of atomic query operations."""
    
    # Data extraction steps
    EXTRACT_DATE = "extract_date"      # Parse a date from query
    LOOKUP_METRIC = "lookup_metric"    # Find a specific metric value
    LOOKUP_SERIES = "lookup_series"    # Find multiple values over time
    
    # Aggregation steps
    SUM = "sum"                        # Sum values
    AVERAGE = "average"                # Average values
    COUNT = "count"                    # Count occurrences
    
    # Calculation steps
    CALCULATE_RATIO = "calculate_ratio"  # Divide one value by another
    CALCULATE_CHANGE = "calculate_change"  # Calculate % change
    CALCULATE_GROWTH = "calculate_growth"  # Calculate YoY/QoQ growth
    
    # Comparison steps
    COMPARE = "compare"                # Compare two values
    RANK = "rank"                     # Rank multiple items
    FIND_MAX = "find_max"             # Find maximum
    FIND_MIN = "find_min"             # Find minimum
    
    # Output steps
    FORMAT_ANSWER = "format_answer"    # Generate final answer
    GENERATE_CHART = "generate_chart"  # Generate visualization


@dataclass
class QueryStep:
    """A single atomic step in query execution."""
    
    step_id: int
    step_type: StepType
    description: str
    
    # Input parameters
    metric_name: Optional[str] = None
    date_filter: Optional[NormalizedDate] = None
    date_text: Optional[str] = None  # Original date text from query
    period_type: Optional[str] = None  # "day", "quarter", "year"
    
    # Dependencies (step IDs this step depends on)
    depends_on: List[int] = field(default_factory=list)
    
    # Output (filled after execution)
    result: Any = None
    confidence: float = 0.0
    error: Optional[str] = None
    
    def is_ready(self, completed_steps: set) -> bool:
        """Check if all dependencies are satisfied."""
        return all(dep in completed_steps for dep in self.depends_on)


@dataclass
class DecomposedQuery:
    """A complex query broken into atomic steps."""
    
    original_query: str
    steps: List[QueryStep]
    primary_intent: str  # "lookup", "compare", "trend", "aggregate"
    
    # Optional extracted info
    metrics_mentioned: List[str] = field(default_factory=list)
    dates_mentioned: List[NormalizedDate] = field(default_factory=list)
    
    def get_execution_order(self) -> List[int]:
        """Return step IDs in topological order for execution."""
        executed = set()
        order = []
        
        while len(order) < len(self.steps):
            for step in self.steps:
                if step.step_id not in executed and step.is_ready(executed):
                    order.append(step.step_id)
                    executed.add(step.step_id)
                    break
        
        return order


class QueryDecomposer:
    """
    Decomposes complex financial queries into atomic operations.
    
    Uses pattern matching for common query types, with optional LLM fallback
    for unusual queries.
    """
    
    # Common metric patterns
    METRIC_PATTERNS = {
        "revenue": ["revenue", "sales", "top line", "net sales", "total sales"],
        "profit": ["profit", "net income", "earnings", "bottom line", "net profit"],
        "margin": ["margin", "profit margin", "gross margin", "operating margin"],
        "cash": ["cash", "cash flow", "cash position", "liquidity"],
        "burn_rate": ["burn rate", "burn", "cash burn", "runway"],
        "expenses": ["expenses", "costs", "operating expenses", "opex"],
        "growth": ["growth", "increase", "change", "yoy", "year over year"],
        "eps": ["eps", "earnings per share"],
    }
    
    # Intent patterns
    INTENT_PATTERNS = {
        "compare": [r"compare", r"vs\.?", r"versus", r"difference", r"between"],
        "trend": [r"trend", r"over time", r"history", r"historical", r"past \d+"],
        "aggregate": [r"total", r"sum", r"average", r"avg", r"mean"],
        "lookup": [r"what is", r"what's", r"show me", r"find", r"get"],
        "calculate": [r"calculate", r"compute", r"derive", r"work out"],
    }
    
    def __init__(self):
        self.date_normalizer = FinancialDateNormalizer()
    
    def decompose(self, query: str) -> DecomposedQuery:
        """
        Decompose a query into atomic steps.
        
        Args:
            query: The user's question
            
        Returns:
            DecomposedQuery with ordered steps
        """
        query_lower = query.lower()
        
        # Extract dates mentioned in query
        dates = self._extract_dates(query)
        
        # Extract metrics mentioned
        metrics = self._extract_metrics(query_lower)
        
        # Determine primary intent
        intent = self._determine_intent(query_lower)
        
        # Generate steps based on query structure
        steps = self._generate_steps(query, query_lower, dates, metrics, intent)
        
        return DecomposedQuery(
            original_query=query,
            steps=steps,
            primary_intent=intent,
            metrics_mentioned=metrics,
            dates_mentioned=dates
        )
    
    def _extract_dates(self, query: str) -> List[NormalizedDate]:
        """Extract all date references from the query."""
        return self.date_normalizer.extract_all_dates(query)
    
    def _extract_metrics(self, query_lower: str) -> List[str]:
        """Extract metric names mentioned in the query."""
        found = []
        for metric_name, keywords in self.METRIC_PATTERNS.items():
            for kw in keywords:
                if kw in query_lower:
                    found.append(metric_name)
                    break
        return found
    
    def _determine_intent(self, query_lower: str) -> str:
        """Determine the primary intent of the query."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        return "lookup"  # Default to simple lookup
    
    def _generate_steps(
        self, 
        query: str,
        query_lower: str,
        dates: List[NormalizedDate], 
        metrics: List[str],
        intent: str
    ) -> List[QueryStep]:
        """Generate execution steps based on query analysis."""
        steps = []
        step_id = 1
        
        # Step 1: Always extract dates first if they exist
        date_step_ids = []
        for date in dates:
            steps.append(QueryStep(
                step_id=step_id,
                step_type=StepType.EXTRACT_DATE,
                description=f"Parse date: {date.original_text}",
                date_filter=date,
                date_text=date.original_text
            ))
            date_step_ids.append(step_id)
            step_id += 1
        
        # Step 2: Generate metric lookup steps
        metric_step_ids = {}
        for metric in metrics:
            deps = date_step_ids.copy() if dates else []
            
            if intent == "trend":
                # For trends, get series data
                steps.append(QueryStep(
                    step_id=step_id,
                    step_type=StepType.LOOKUP_SERIES,
                    description=f"Get {metric} time series",
                    metric_name=metric,
                    depends_on=deps
                ))
            else:
                # For single values or comparisons
                if dates:
                    for i, date in enumerate(dates):
                        steps.append(QueryStep(
                            step_id=step_id,
                            step_type=StepType.LOOKUP_METRIC,
                            description=f"Look up {metric} for {date.original_text}",
                            metric_name=metric,
                            date_filter=date,
                            depends_on=[date_step_ids[i]] if i < len(date_step_ids) else []
                        ))
                        metric_step_ids[f"{metric}_{date.original_text}"] = step_id
                        step_id += 1
                else:
                    steps.append(QueryStep(
                        step_id=step_id,
                        step_type=StepType.LOOKUP_METRIC,
                        description=f"Look up latest {metric}",
                        metric_name=metric
                    ))
                    metric_step_ids[metric] = step_id
                    step_id += 1
        
        # Step 3: Generate computation steps based on intent
        if intent == "compare" and len(metric_step_ids) >= 2:
            # Compare values
            deps = list(metric_step_ids.values())[-2:]
            steps.append(QueryStep(
                step_id=step_id,
                step_type=StepType.COMPARE,
                description="Compare values",
                depends_on=deps
            ))
            step_id += 1
        
        elif intent == "aggregate":
            # Aggregate values
            if "average" in query_lower or "avg" in query_lower:
                steps.append(QueryStep(
                    step_id=step_id,
                    step_type=StepType.AVERAGE,
                    description="Calculate average",
                    depends_on=list(metric_step_ids.values())
                ))
            else:
                steps.append(QueryStep(
                    step_id=step_id,
                    step_type=StepType.SUM,
                    description="Calculate sum",
                    depends_on=list(metric_step_ids.values())
                ))
            step_id += 1
        
        # Step 4: Handle growth/change calculations
        if "growth" in query_lower or "change" in query_lower or "yoy" in query_lower:
            if len(metric_step_ids) >= 1:
                steps.append(QueryStep(
                    step_id=step_id,
                    step_type=StepType.CALCULATE_GROWTH,
                    description="Calculate growth rate",
                    depends_on=list(metric_step_ids.values())
                ))
                step_id += 1
        
        # Handle burn rate specifically
        if "burn" in query_lower:
            cash_steps = [sid for key, sid in metric_step_ids.items() if "cash" in key.lower()]
            if cash_steps:
                steps.append(QueryStep(
                    step_id=step_id,
                    step_type=StepType.CALCULATE_CHANGE,
                    description="Calculate burn rate (cash change over period)",
                    metric_name="burn_rate",
                    depends_on=cash_steps
                ))
                step_id += 1
        
        # Handle ratio calculations
        if "margin" in query_lower or "ratio" in query_lower:
            if "profit" in metrics and "revenue" in metrics:
                profit_step = metric_step_ids.get("profit")
                rev_step = metric_step_ids.get("revenue")
                if profit_step and rev_step:
                    steps.append(QueryStep(
                        step_id=step_id,
                        step_type=StepType.CALCULATE_RATIO,
                        description="Calculate profit margin (profit/revenue)",
                        depends_on=[profit_step, rev_step]
                    ))
                    step_id += 1
        
        # Final step: Format answer
        all_step_ids = [s.step_id for s in steps]
        if all_step_ids:
            steps.append(QueryStep(
                step_id=step_id,
                step_type=StepType.FORMAT_ANSWER,
                description="Format final answer",
                depends_on=[all_step_ids[-1]] if all_step_ids else []
            ))
        
        # If no steps generated, create a simple lookup
        if len(steps) <= 1:
            steps = [
                QueryStep(
                    step_id=1,
                    step_type=StepType.LOOKUP_METRIC,
                    description=f"Search for: {query}",
                    metric_name=query[:50]  # Use query as search term
                ),
                QueryStep(
                    step_id=2,
                    step_type=StepType.FORMAT_ANSWER,
                    description="Format answer from search results",
                    depends_on=[1]
                )
            ]
        
        return steps
    
    def get_step_dependencies_graph(self, decomposed: DecomposedQuery) -> Dict[int, List[int]]:
        """Return dependency graph for visualization."""
        return {step.step_id: step.depends_on for step in decomposed.steps}
    
    def explain_decomposition(self, decomposed: DecomposedQuery) -> str:
        """Generate human-readable explanation of the decomposition."""
        lines = [
            f"Query: {decomposed.original_query}",
            f"Intent: {decomposed.primary_intent}",
            f"Metrics: {', '.join(decomposed.metrics_mentioned) or 'auto-detect'}",
            f"Dates: {', '.join(str(d) for d in decomposed.dates_mentioned) or 'auto-detect'}",
            "",
            "Execution Steps:"
        ]
        
        for step in decomposed.steps:
            deps = f" (depends on: {step.depends_on})" if step.depends_on else ""
            lines.append(f"  {step.step_id}. [{step.step_type.value}] {step.description}{deps}")
        
        return "\n".join(lines)


# Convenience function
def decompose_query(query: str) -> DecomposedQuery:
    """Quick helper to decompose a query."""
    return QueryDecomposer().decompose(query)


def is_complex_query(query: str) -> bool:
    """
    Check if a query is complex enough to warrant decomposition.
    
    Simple queries (single metric lookup) don't need decomposition.
    """
    decomposer = QueryDecomposer()
    query_lower = query.lower()
    
    dates = decomposer._extract_dates(query)
    metrics = decomposer._extract_metrics(query_lower)
    intent = decomposer._determine_intent(query_lower)
    
    # Complex if:
    # - Multiple dates mentioned
    # - Multiple metrics mentioned
    # - Intent is compare, trend, or aggregate
    # - Contains calculation keywords
    
    if len(dates) > 1:
        return True
    if len(metrics) > 1:
        return True
    if intent in ("compare", "trend", "aggregate", "calculate"):
        return True
    
    calc_keywords = ["burn rate", "growth", "change", "ratio", "percent", "%", "vs", "compare"]
    if any(kw in query_lower for kw in calc_keywords):
        return True
    
    return False
