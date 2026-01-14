# src/analysis/statement_classifier.py
"""
Financial Statement Classifier
Identifies the type of financial statement from table content.

Types:
- Income Statement / Statement of Operations
- Balance Sheet / Statement of Financial Position  
- Cash Flow Statement
- Statement of Changes in Equity
- Notes / Supplementary
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd


class StatementType(Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    EQUITY_CHANGE = "equity_change"
    SEGMENT_DATA = "segment_data"
    NOTES = "notes"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of statement classification."""
    
    statement_type: StatementType
    confidence: float  # 0.0 - 1.0
    matched_keywords: List[str]
    title_hint: Optional[str] = None


# Keyword signatures for each statement type
# Weight indicates importance (higher = more definitive)
STATEMENT_SIGNATURES: Dict[StatementType, Dict[str, float]] = {
    StatementType.INCOME_STATEMENT: {
        # Row labels (weighted by specificity)
        "total revenue": 3.0,
        "net revenue": 3.0,
        "net sales": 3.0,
        "total net sales": 3.0,
        "cost of revenue": 2.5,
        "cost of sales": 2.5,
        "cost of goods sold": 2.5,
        "gross profit": 2.5,
        "gross margin": 2.5,
        "operating income": 2.0,
        "operating expenses": 2.0,
        "income from operations": 2.0,
        "interest expense": 1.5,
        "income before": 2.0,
        "provision for income taxes": 2.0,
        "income tax expense": 2.0,
        "net income": 2.5,
        "net loss": 2.5,
        "earnings per share": 3.0,
        "basic eps": 3.0,
        "diluted eps": 3.0,
        "research and development": 1.5,
        "selling, general": 1.5,
        # Title keywords
        "statement of operations": 5.0,
        "income statement": 5.0,
        "statements of operations": 5.0,
        "profit and loss": 4.0,
        "results of operations": 4.0,
    },
    
    StatementType.BALANCE_SHEET: {
        # Row labels
        "total assets": 4.0,
        "current assets": 3.0,
        "non-current assets": 3.0,
        "total liabilities": 4.0,
        "current liabilities": 3.0,
        "non-current liabilities": 3.0,
        "stockholders' equity": 4.0,
        "shareholders' equity": 4.0,
        "total equity": 3.5,
        "retained earnings": 2.5,
        "accounts receivable": 2.0,
        "accounts payable": 2.0,
        "inventory": 1.5,
        "property, plant": 2.0,
        "property and equipment": 2.0,
        "long-term debt": 2.0,
        "common stock": 2.0,
        "accumulated deficit": 2.0,
        "cash and cash equivalents": 2.0,
        "marketable securities": 1.5,
        "goodwill": 1.5,
        "intangible assets": 1.5,
        # Title keywords
        "balance sheet": 5.0,
        "statement of financial position": 5.0,
        "consolidated balance": 5.0,
    },
    
    StatementType.CASH_FLOW: {
        # Row labels
        "cash flows from operating": 5.0,
        "operating activities": 4.0,
        "cash flows from investing": 5.0,
        "investing activities": 4.0,
        "cash flows from financing": 5.0,
        "financing activities": 4.0,
        "net cash provided": 3.5,
        "net cash used": 3.5,
        "net cash generated": 3.5,
        "depreciation and amortization": 2.0,
        "changes in operating assets": 2.0,
        "capital expenditures": 2.0,
        "purchases of property": 2.0,
        "proceeds from": 1.5,
        "repurchases of common stock": 2.0,
        "dividends paid": 2.0,
        "payments for": 1.5,
        "effect of exchange rate": 1.5,
        "increase in cash": 2.0,
        "decrease in cash": 2.0,
        "cash at beginning": 2.5,
        "cash at end": 2.5,
        # Title keywords
        "cash flow statement": 5.0,
        "statement of cash flows": 5.0,
        "cash flows": 4.0,
    },
    
    StatementType.EQUITY_CHANGE: {
        "beginning balance": 2.0,
        "ending balance": 2.0,
        "issuance of common stock": 3.0,
        "stock-based compensation": 2.0,
        "comprehensive income": 3.0,
        "other comprehensive": 2.5,
        "treasury stock": 2.0,
        "statement of stockholders": 5.0,
        "statement of shareholders": 5.0,
        "changes in equity": 5.0,
    },
    
    StatementType.SEGMENT_DATA: {
        "by segment": 4.0,
        "segment information": 4.0,
        "reportable segments": 4.0,
        "geographic": 2.0,
        "by region": 3.0,
        "by product": 3.0,
        "americas": 2.0,
        "europe": 2.0,
        "asia": 2.0,
        "greater china": 2.5,
        "rest of asia": 2.0,
        "iphone": 3.0,  # Apple-specific but useful
        "mac": 2.0,
        "ipad": 2.0,
        "services": 1.5,
        "wearables": 2.0,
    },
}


class StatementClassifier:
    """
    Classifies extracted tables into financial statement types.
    
    Uses weighted keyword matching + structural analysis.
    """
    
    def __init__(self, min_confidence: float = 0.3):
        """
        Args:
            min_confidence: Minimum confidence to return a non-UNKNOWN type
        """
        self.min_confidence = min_confidence
        self.signatures = STATEMENT_SIGNATURES
    
    def classify(self, df: pd.DataFrame, title_hint: str = None) -> ClassificationResult:
        """
        Classify a DataFrame as a financial statement type.
        
        Args:
            df: Extracted table DataFrame
            title_hint: Optional title/header text from the document
            
        Returns:
            ClassificationResult with type, confidence, and matched keywords
        """
        # Combine all text for matching
        text_corpus = self._build_text_corpus(df, title_hint)
        text_lower = text_corpus.lower()
        
        scores: Dict[StatementType, Tuple[float, List[str]]] = {}
        
        for stmt_type, keywords in self.signatures.items():
            total_score = 0.0
            matched = []
            
            for keyword, weight in keywords.items():
                if keyword in text_lower:
                    total_score += weight
                    matched.append(keyword)
            
            scores[stmt_type] = (total_score, matched)
        
        # Find best match
        best_type = StatementType.UNKNOWN
        best_score = 0.0
        best_matched = []
        
        for stmt_type, (score, matched) in scores.items():
            if score > best_score:
                best_score = score
                best_type = stmt_type
                best_matched = matched
        
        # Normalize confidence (based on typical max scores)
        max_possible = 25.0  # Reasonable max for a well-formatted statement
        confidence = min(best_score / max_possible, 1.0)
        
        # Apply minimum confidence threshold
        if confidence < self.min_confidence:
            best_type = StatementType.UNKNOWN
        
        return ClassificationResult(
            statement_type=best_type,
            confidence=confidence,
            matched_keywords=best_matched,
            title_hint=title_hint
        )
    
    def classify_all(self, tables: List[Dict]) -> List[Tuple[Dict, ClassificationResult]]:
        """
        Classify multiple tables.
        
        Args:
            tables: List of table dicts with 'df' key
            
        Returns:
            List of (table_dict, classification) tuples
        """
        results = []
        for table in tables:
            df = table.get('df')
            title = table.get('title') or table.get('markdown', '')[:200]
            
            if df is not None:
                classification = self.classify(df, title)
                results.append((table, classification))
        
        return results
    
    def _build_text_corpus(self, df: pd.DataFrame, title_hint: str = None) -> str:
        """Build searchable text corpus from DataFrame."""
        parts = []
        
        # Add title hint first (highest priority)
        if title_hint:
            parts.append(title_hint)
        
        # Add column headers
        parts.extend([str(col) for col in df.columns])
        
        # Add first column values (usually row labels)
        if len(df.columns) > 0:
            first_col = df.iloc[:, 0].astype(str).tolist()
            parts.extend(first_col)
        
        # Add a sample of other values for context
        if len(df.columns) > 1:
            sample_values = df.iloc[:10, 1:].astype(str).values.flatten().tolist()
            parts.extend(sample_values[:50])
        
        return " ".join(parts)
    
    def get_core_statements(self, tables: List[Dict]) -> Dict[StatementType, List[Dict]]:
        """
        Get the core financial statements from a list of tables.
        Returns the best match for each statement type.
        """
        classified = self.classify_all(tables)
        
        # Group by statement type, keeping highest confidence
        by_type: Dict[StatementType, List[Tuple[Dict, ClassificationResult]]] = {}
        
        for table, result in classified:
            if result.statement_type not in by_type:
                by_type[result.statement_type] = []
            by_type[result.statement_type].append((table, result))
        
        # Sort each group by confidence and return
        grouped: Dict[StatementType, List[Dict]] = {}
        for stmt_type, items in by_type.items():
            sorted_items = sorted(items, key=lambda x: x[1].confidence, reverse=True)
            grouped[stmt_type] = [item[0] for item in sorted_items]
        
        return grouped


# Convenience function
def classify_statement(df: pd.DataFrame, title: str = None) -> StatementType:
    """Quick helper to classify a single table."""
    result = StatementClassifier().classify(df, title)
    return result.statement_type


def get_statement_priority(stmt_type: StatementType) -> int:
    """Get priority for statement type (higher = more important for core analysis)."""
    priorities = {
        StatementType.INCOME_STATEMENT: 5,
        StatementType.BALANCE_SHEET: 4,
        StatementType.CASH_FLOW: 4,
        StatementType.EQUITY_CHANGE: 2,
        StatementType.SEGMENT_DATA: 3,
        StatementType.NOTES: 1,
        StatementType.UNKNOWN: 0,
    }
    return priorities.get(stmt_type, 0)
