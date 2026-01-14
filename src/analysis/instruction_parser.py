# src/analysis/instruction_parser.py
"""
Instructed Retriever: Instruction Parser

Extracts structured retrieval constraints from natural language queries.
Implements Databricks-style instruction propagation for RAG pre-filtering.
"""

import re
from typing import Dict, Any, Optional, List

# ===== KNOWN PATTERNS =====

# Period patterns (quarters, fiscal years, date ranges)
QUARTER_PATTERN = re.compile(
    r'\b(Q[1-4]|first|second|third|fourth)\s*(quarter)?\s*(of\s*)?(FY\s*)?(20\d{2})\b',
    re.IGNORECASE
)
FISCAL_YEAR_PATTERN = re.compile(r'\b(FY|fiscal\s*year)\s*(20\d{2})\b', re.IGNORECASE)
MONTH_YEAR_PATTERN = re.compile(
    r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
    r'\s*(?:\d{1,2},?\s*)?(20\d{2})\b',
    re.IGNORECASE
)
THREE_SIX_MONTH_PATTERN = re.compile(
    r'\b(three|six|3|6)\s*months?\s*(ended|ending)?\b',
    re.IGNORECASE
)

# Statement type inference keywords
INCOME_STATEMENT_KEYWORDS = [
    "revenue", "sales", "net sales", "profit", "loss", "profitable", "profitability",
    "net income", "earnings", "eps", "earnings per share", "operating income",
    "gross margin", "gross profit", "cost of sales", "cogs", "cost of revenue",
    "r&d", "research", "development", "sg&a", "operating expense", "expense",
    "income statement", "statement of operations", "ebit", "ebitda",
    "making money", "losing money", "bottom line"
]

BALANCE_SHEET_KEYWORDS = [
    "assets", "liabilities", "equity", "debt", "cash", "cash position",
    "balance sheet", "accounts receivable", "receivable", "accounts payable",
    "payable", "inventory", "current assets", "current liabilities",
    "working capital", "total assets", "total liabilities", "shareholders equity",
    "stockholders equity", "net worth", "leverage"
]

CASH_FLOW_KEYWORDS = [
    "cash flow", "cash flows", "operating cash flow", "free cash flow", "fcf",
    "cash from operations", "cash generated", "cash provided", "cash used",
    "capital expenditure", "capex", "investing activities", "financing activities",
    "statement of cash flows"
]

SEGMENT_KEYWORDS = [
    "segment", "product", "geographic", "region", "country", "breakdown",
    "by product", "by region", "by segment", "product line"
]

# Known segments (from question_router.py - keep in sync)
KNOWN_SEGMENTS = [
    "americas", "europe", "greater china", "japan", "rest of asia pacific", 
    "asia pacific", "china", "united states", "u.s.", "international",
    "iphone", "mac", "ipad", "wearables", "services", "home", "accessories"
]


def parse_instructions(query: str) -> Dict[str, Any]:
    """
    Extract structured retrieval instructions from a natural language query.
    
    This is the core of the Instructed Retriever approach - parsing user intent
    into metadata filters that can be applied BEFORE embedding search.
    
    Args:
        query: Natural language financial question
        
    Returns:
        Dictionary with:
        - period_filter: str | None - Specific period constraint (e.g., "Q2 2025")
        - period_type: str | None - "three_months" | "six_months" | None
        - stmt_type_filter: str | None - Statement type to prioritize
        - segment_filter: str | None - Business segment or region
        - priority: str | None - "core" (main statements) | "footnotes"
        - keywords: List[str] - Additional search terms extracted
        - confidence: float - Confidence in instruction extraction (0-1)
    """
    q = query.lower().strip()
    instructions = {
        "period_filter": None,
        "period_type": None,
        "stmt_type_filter": None,
        "segment_filter": None,
        "priority": None,
        "keywords": [],
        "confidence": 0.0
    }
    
    confidence_factors = []
    
    # ===== 1. PERIOD EXTRACTION =====
    period_filter = _extract_period(q)
    if period_filter:
        instructions["period_filter"] = period_filter
        confidence_factors.append(0.3)
    
    # Check for 3-month vs 6-month preference
    period_type = _extract_period_type(q)
    if period_type:
        instructions["period_type"] = period_type
        confidence_factors.append(0.1)
    
    # ===== 2. STATEMENT TYPE INFERENCE =====
    stmt_type = _infer_statement_type(q)
    if stmt_type:
        instructions["stmt_type_filter"] = stmt_type
        confidence_factors.append(0.3)
    
    # ===== 3. SEGMENT DETECTION =====
    segment = _detect_segment(q)
    if segment:
        instructions["segment_filter"] = segment
        confidence_factors.append(0.2)
    
    # ===== 4. PRIORITY (CORE vs FOOTNOTES) =====
    if any(kw in q for kw in ["note", "footnote", "details", "breakdown", "disclosure"]):
        instructions["priority"] = "footnotes"
    else:
        instructions["priority"] = "core"
    
    # ===== 5. EXTRACT ADDITIONAL KEYWORDS =====
    instructions["keywords"] = _extract_financial_keywords(q)
    
    # Calculate confidence
    instructions["confidence"] = min(1.0, sum(confidence_factors))
    
    return instructions


def _extract_period(query: str) -> Optional[str]:
    """Extract period constraint from query."""
    
    # Try quarter pattern first (most specific)
    match = QUARTER_PATTERN.search(query)
    if match:
        quarter_word = match.group(1).upper()
        year = match.group(5) if match.group(5) else ""
        
        # Normalize quarter
        quarter_map = {"FIRST": "Q1", "SECOND": "Q2", "THIRD": "Q3", "FOURTH": "Q4"}
        quarter = quarter_map.get(quarter_word, quarter_word)
        
        if year:
            return f"{quarter} {year}"
        return quarter
    
    # Try fiscal year
    match = FISCAL_YEAR_PATTERN.search(query)
    if match:
        return f"FY {match.group(2)}"
    
    # Try month/year
    match = MONTH_YEAR_PATTERN.search(query)
    if match:
        month = match.group(1).capitalize()  # Preserve capitalization
        year = match.group(2)
        return f"{month} {year}"
    
    # Try just year
    year_match = re.search(r'\b(20\d{2})\b', query)
    if year_match:
        return year_match.group(1)
    
    return None


def _extract_period_type(query: str) -> Optional[str]:
    """Detect if query specifies 3-month or 6-month period."""
    match = THREE_SIX_MONTH_PATTERN.search(query)
    if match:
        num = match.group(1).lower()
        if num in ["three", "3"]:
            return "three_months"
        elif num in ["six", "6"]:
            return "six_months"
    return None


def _infer_statement_type(query: str) -> Optional[str]:
    """Infer which financial statement is most relevant."""
    
    # Score each statement type - use weighted scoring
    # Cash flow keywords should outweigh balance sheet "cash" keyword
    income_score = sum(1 for kw in INCOME_STATEMENT_KEYWORDS if kw in query)
    balance_score = sum(1 for kw in BALANCE_SHEET_KEYWORDS if kw in query)
    
    # Weight cash flow keywords higher (2 points each)
    cash_flow_score = sum(2 for kw in CASH_FLOW_KEYWORDS if kw in query)
    
    segment_score = sum(1 for kw in SEGMENT_KEYWORDS if kw in query)
    
    # Find max
    scores = {
        "Income Statement": income_score,
        "Balance Sheet": balance_score,
        "Cash Flow Statement": cash_flow_score,
        "Segment Info": segment_score
    }
    
    max_score = max(scores.values())
    if max_score == 0:
        return None
    
    # Return the statement type with highest score
    for stmt, score in scores.items():
        if score == max_score:
            return stmt
    
    return None


def _detect_segment(query: str) -> Optional[str]:
    """Detect business segment or geographic region filter."""
    # Sort by length descending to match "Greater China" before "China"
    sorted_segments = sorted(KNOWN_SEGMENTS, key=len, reverse=True)
    
    for seg in sorted_segments:
        if seg in query:
            return seg.title()  # Return properly capitalized
    
    return None


def _extract_financial_keywords(query: str) -> List[str]:
    """Extract important financial terms for query enhancement."""
    keywords = []
    
    # Add matched metric keywords
    all_keywords = (
        INCOME_STATEMENT_KEYWORDS + 
        BALANCE_SHEET_KEYWORDS + 
        CASH_FLOW_KEYWORDS
    )
    
    for kw in all_keywords:
        if kw in query and kw not in keywords:
            keywords.append(kw)
    
    return keywords[:5]  # Limit to top 5 to avoid noise


def build_chroma_where_filter(
    instructions: Dict[str, Any],
    source_filter: Optional[List[str]] = None
) -> Optional[Dict]:
    """
    Build a ChromaDB `where` filter from parsed instructions.
    
    ChromaDB supports:
    - $eq, $ne: equality/inequality
    - $gt, $gte, $lt, $lte: comparisons
    - $in, $nin: membership
    - $and, $or: logical
    - $contains: substring (for some versions)
    
    Args:
        instructions: Parsed instructions from parse_instructions()
        source_filter: Optional list of source file names
        
    Returns:
        ChromaDB where filter dict, or None if no filters apply
    """
    conditions = []
    
    # Statement type filter
    if instructions.get("stmt_type_filter"):
        stmt = instructions["stmt_type_filter"]
        conditions.append({"stmt_type": {"$eq": stmt}})
    
    # Source filter (session isolation)
    if source_filter and len(source_filter) == 1:
        conditions.append({"source": {"$eq": source_filter[0]}})
    elif source_filter and len(source_filter) > 1:
        conditions.append({"source": {"$in": source_filter}})
    
    # Period filter - ChromaDB string matching is limited
    # We use $contains if available, otherwise skip (handle in post-filtering)
    # Note: ChromaDB's $contains may not be available in all versions
    # For robustness, we'll rely on post-hoc filtering for period
    
    # Build final filter
    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


# ===== UTILITY FUNCTIONS =====

def format_instructions_log(instructions: Dict[str, Any]) -> str:
    """Format instructions for logging."""
    parts = []
    if instructions.get("period_filter"):
        parts.append(f"Period: {instructions['period_filter']}")
    if instructions.get("period_type"):
        parts.append(f"Type: {instructions['period_type']}")
    if instructions.get("stmt_type_filter"):
        parts.append(f"Statement: {instructions['stmt_type_filter']}")
    if instructions.get("segment_filter"):
        parts.append(f"Segment: {instructions['segment_filter']}")
    if instructions.get("priority"):
        parts.append(f"Priority: {instructions['priority']}")
    
    if parts:
        return f"📋 [INSTRUCTIONS] {' | '.join(parts)} (conf: {instructions['confidence']:.0%})"
    return "📋 [INSTRUCTIONS] No specific constraints detected"
