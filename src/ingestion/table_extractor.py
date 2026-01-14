import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

# Import our new modules
from src.analysis.date_normalizer import FinancialDateNormalizer, NormalizedDate, extract_dates_from_text
from src.analysis.statement_classifier import StatementClassifier, StatementType, ClassificationResult


@dataclass
class CellProvenance:
    """Tracks the exact source of a cell value."""
    page: int
    row_index: int
    col_index: int
    row_label: str  # First column value (usually the metric name)
    col_label: str  # Column header
    raw_text: str   # Original text before any cleaning
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)


@dataclass  
class EnhancedTable:
    """A table with rich metadata for accurate retrieval."""
    
    df: pd.DataFrame
    page: int
    source_file: str = ""
    markdown: str = ""
    
    # Classification
    statement_type: StatementType = StatementType.UNKNOWN
    classification_confidence: float = 0.0
    
    # Dates found in headers
    periods: List[NormalizedDate] = field(default_factory=list)
    date_columns: Dict[str, NormalizedDate] = field(default_factory=dict)  # col_name -> normalized date
    
    # Provenance (optional, for verification)
    provenance: Dict[Tuple[int, int], CellProvenance] = field(default_factory=dict)
    
    # Row labels (first column, usually metric names)
    row_labels: List[str] = field(default_factory=list)
    
    # Context (Fused Text)
    preceding_text: str = ""
    following_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        return {
            "df": self.df,
            "page": self.page,
            "source_file": self.source_file,
            "markdown": self.markdown,
            "statement_type": self.statement_type.value,
            "classification_confidence": self.classification_confidence,
            "periods": [str(p) for p in self.periods],
            "date_columns": {k: str(v) for k, v in self.date_columns.items()},
            "row_labels": self.row_labels,
            "preceding_text": self.preceding_text,
            "following_text": self.following_text,
        }


def extract_tables(pdf_path: str, track_provenance: bool = False) -> List[Dict]:
    """
    Extract all tables from a PDF file with enhanced metadata.
    
    Args:
        pdf_path: Path to PDF file
        track_provenance: If True, track cell-level provenance (slower but enables verification)
    
    Returns:
        List of dicts with keys: df, page, markdown, statement_type, periods, date_columns, row_labels
    """
    tables = []
    classifier = StatementClassifier()
    date_normalizer = FinancialDateNormalizer()
    source_file = Path(pdf_path).name
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            
            # Extract page text for title detection
            page_text = page.extract_text() or ""
            
            # Use "text" strategy for better columnar alignment in financial docs
            page_tables = page.extract_tables(table_settings={
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
            })
            
            for table_idx, table in enumerate(page_tables):
                if not table:  # Skip empty tables
                    continue
                    
                # Create DataFrame from table (list of rows)
                df = pd.DataFrame(table)
                
                # Remove completely empty rows and columns
                df = df.dropna(how="all", axis=1)
                df = df.dropna(how="all", axis=0)
                
                if df.empty:
                    continue
                
                # Build enhanced table
                enhanced = EnhancedTable(
                    df=df,
                    page=page_num,
                    source_file=source_file
                )

                # Extract Surrounding Context (Text before/after table)
                # This is critical for connecting tables to their "Notes" (e.g. Note 10)
                # We use the bbox of the table to find text above/below it
                bbox = table_bbox(page, table)
                if bbox:
                    # Context Window: 300px above (approx 1/3 page), 100px below
                    enhanced.preceding_text = _extract_text_around_table(page, bbox, region="above", margin=300)
                    enhanced.following_text = _extract_text_around_table(page, bbox, region="below", margin=100)
                
                # Extract row labels (first column)
                if len(df.columns) > 0:
                    enhanced.row_labels = df.iloc[:, 0].astype(str).tolist()
                
                # Detect dates in column headers
                _extract_column_dates(df, enhanced, date_normalizer)
                
                # Classify statement type
                # Use page text AND preceding text as title hint
                # Preceding text is much stronger signal (e.g. "Note 5. Inventories")
                title_hint = _find_table_title(enhanced.preceding_text + "\n" + page_text, table_idx)
                classification = classifier.classify(df, title_hint)
                enhanced.statement_type = classification.statement_type
                enhanced.classification_confidence = classification.confidence
                
                # Generate markdown with metadata header AND context
                enhanced.markdown = to_markdown_string(
                    df, 
                    statement_type=enhanced.statement_type,
                    periods=enhanced.periods,
                    context=enhanced.preceding_text  # Pass context to be embedded in Markdown
                )
                
                # Optional: Track cell provenance
                if track_provenance:
                    _track_provenance(df, enhanced, table, page_num)
                
                # Append as dict for backward compatibility
                tables.append(enhanced.to_dict())
    
    return tables


def table_bbox(page, table_data) -> Optional[Tuple[float, float, float, float]]:
    """Estimate table bounding box from its cell data."""
    # pdfplumber extract_tables returns simple data, not bboxes. 
    # We need to find the table in page.find_tables() to get bbox.
    # This is a heuristic match.
    tables = page.find_tables()
    for t in tables:
        # Check if dimensions match fairly well
        if len(t.extract()) == len(table_data):
            return t.bbox
    return None

def _extract_text_around_table(page, table_bbox, region="above", margin=100) -> str:
    """Extract text immediately above or below a table."""
    x0, y0, x1, y1 = table_bbox
    page_height = page.height
    
    if region == "above":
        # Search area: from Top of page (or higher) down to Table Top (y0)
        # Limit lookback by 'margin'
        search_y0 = max(0, y0 - margin)
        search_y1 = y0
        search_bbox = (0, search_y0, page.width, search_y1)
    else:
        # Search area: from Table Bottom (y1) down to margin
        search_y0 = y1
        search_y1 = min(page_height, y1 + margin)
        search_bbox = (0, search_y0, page.width, search_y1)
        
    text = page.within_bbox(search_bbox).extract_text()
    return text.strip() if text else ""

def extract_tables_enhanced(pdf_path: str) -> List[EnhancedTable]:
    """
    Extract tables with full EnhancedTable objects (not dicts).
    Use this for advanced processing that needs full provenance.
    """
    raw_tables = extract_tables(pdf_path, track_provenance=True)
    # Re-extract with EnhancedTable objects
    # (This is a simplified version - in production, refactor to avoid double extraction)
    return [_dict_to_enhanced(t) for t in raw_tables]


def _extract_column_dates(df: pd.DataFrame, enhanced: EnhancedTable, normalizer: FinancialDateNormalizer):
    """Extract and normalize dates from column headers."""
    for col_idx, col in enumerate(df.columns):
        col_str = str(col)
        
        # Try to parse as date
        normalized = normalizer.parse(col_str)
        if normalized:
            enhanced.date_columns[col_str] = normalized
            enhanced.periods.append(normalized)
        else:
            # Check for dates within the column text
            dates = normalizer.extract_all_dates(col_str)
            for d in dates:
                enhanced.date_columns[col_str] = d
                enhanced.periods.append(d)
                break  # Take first date found
    
    # Deduplicate periods
    seen = set()
    unique_periods = []
    for p in enhanced.periods:
        key = (p.start_date, p.end_date)
        if key not in seen:
            seen.add(key)
            unique_periods.append(p)
    enhanced.periods = sorted(unique_periods, key=lambda x: x.start_date)


def _find_table_title(page_text: str, table_idx: int) -> str:
    """
    Try to find a title for the table from page text.
    Looks for common financial statement title patterns.
    """
    title_patterns = [
        r"(?:consolidated\s+)?statements?\s+of\s+operations",
        r"(?:consolidated\s+)?statements?\s+of\s+(?:financial\s+)?(?:position|condition)",
        r"(?:consolidated\s+)?balance\s+sheets?",
        r"(?:consolidated\s+)?statements?\s+of\s+cash\s+flows?",
        r"(?:consolidated\s+)?statements?\s+of\s+(?:stockholders?|shareholders?)['']?\s+equity",
        r"income\s+statements?",
        r"(?:condensed\s+)?(?:consolidated\s+)?financial\s+statements?",
    ]
    
    import re
    for pattern in title_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return ""


def _track_provenance(df: pd.DataFrame, enhanced: EnhancedTable, raw_table: List, page_num: int):
    """Track provenance for each cell."""
    for row_idx, row in enumerate(raw_table):
        if row_idx >= len(df):
            break
        for col_idx, cell in enumerate(row):
            if col_idx >= len(df.columns):
                break
                
            row_label = str(raw_table[row_idx][0]) if raw_table[row_idx] else ""
            col_label = str(df.columns[col_idx])
            
            enhanced.provenance[(row_idx, col_idx)] = CellProvenance(
                page=page_num,
                row_index=row_idx,
                col_index=col_idx,
                row_label=row_label,
                col_label=col_label,
                raw_text=str(cell) if cell else ""
            )


def _dict_to_enhanced(d: Dict) -> EnhancedTable:
    """Convert dict back to EnhancedTable (for internal use)."""
    return EnhancedTable(
        df=d["df"],
        page=d["page"],
        source_file=d.get("source_file", ""),
        markdown=d.get("markdown", ""),
        statement_type=StatementType(d.get("statement_type", "unknown")),
        classification_confidence=d.get("classification_confidence", 0.0),
        row_labels=d.get("row_labels", [])
    )


def to_markdown_string(
    df: pd.DataFrame, 
    statement_type: StatementType = None,
    periods: List[NormalizedDate] = None,
    context: str = None
) -> str:
    """
    Convert DataFrame to Markdown string with optimized formatting for LLMs.
    Includes metadata header for better retrieval.
    """
    try:
        # 1. Clean basics
        df_clean = df.fillna("")
        
        # 2. Build metadata header
        rows, cols = df.shape
        header_parts = [f"Table ({rows} rows x {cols} columns)"]
        
        if statement_type and statement_type != StatementType.UNKNOWN:
            type_labels = {
                StatementType.INCOME_STATEMENT: "Income Statement",
                StatementType.BALANCE_SHEET: "Balance Sheet",
                StatementType.CASH_FLOW: "Cash Flow Statement",
                StatementType.EQUITY_CHANGE: "Statement of Equity",
                StatementType.SEGMENT_DATA: "Segment Data",
            }
            header_parts.append(f"Type: {type_labels.get(statement_type, statement_type.value)}")
        
        if periods:
            period_strs = [str(p) for p in periods[:3]]  # Limit to 3 for brevity
            header_parts.append(f"Periods: {', '.join(period_strs)}")
        
        header = " | ".join(header_parts)
        
        # 3. Convert to markdown
        md = df_clean.to_markdown(index=False, tablefmt="github")
        
        result = f"{header}\n{md}"
        
        # 4. Append Context if available
        if context:
            # Add a "Context Hint" block
            result = f"**Context Hint**: {context[:200]}...\n\n{result}"
            
        return result
    except Exception as e:
        return f"Error converting table to markdown: {str(e)}"


def get_value_with_provenance(
    tables: List[Dict], 
    row_label: str, 
    col_label: str = None,
    statement_type: StatementType = None
) -> Optional[Tuple[Any, CellProvenance]]:
    """
    Find a value by row/column labels and return with provenance.
    
    Args:
        tables: List of table dicts from extract_tables
        row_label: The metric name to find (e.g., "Total Revenue")
        col_label: Optional column to look in (e.g., "Q1 2024")
        statement_type: Optional filter by statement type
        
    Returns:
        (value, provenance) tuple or None
    """
    row_label_lower = row_label.lower()
    
    for table in tables:
        # Filter by statement type if specified
        if statement_type and table.get("statement_type") != statement_type.value:
            continue
            
        df = table.get("df")
        if df is None or df.empty:
            continue
        
        # Search rows
        for idx, label in enumerate(table.get("row_labels", [])):
            if row_label_lower in label.lower():
                # Found the row
                if col_label:
                    # Find specific column
                    for col_idx, col in enumerate(df.columns):
                        if col_label.lower() in str(col).lower():
                            value = df.iloc[idx, col_idx]
                            prov = CellProvenance(
                                page=table.get("page", 0),
                                row_index=idx,
                                col_index=col_idx,
                                row_label=label,
                                col_label=str(col),
                                raw_text=str(value)
                            )
                            return (value, prov)
                else:
                    # Return last numeric column (usually most recent period)
                    for col_idx in range(len(df.columns) - 1, 0, -1):
                        value = df.iloc[idx, col_idx]
                        if value and str(value).strip():
                            prov = CellProvenance(
                                page=table.get("page", 0),
                                row_index=idx,
                                col_index=col_idx,
                                row_label=label,
                                col_label=str(df.columns[col_idx]),
                                raw_text=str(value)
                            )
                            return (value, prov)
    
    return None

