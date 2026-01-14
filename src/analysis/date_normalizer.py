# src/analysis/date_normalizer.py
"""
Financial Date Normalizer
Parses and normalizes various financial date formats for accurate retrieval.

Supported formats:
- Exact dates: "Mar 29", "March 29, 2025", "29-Mar-2025"
- Quarters: "Q1 2024", "Q2", "1Q24"  
- Periods: "Three months ended March 29, 2025"
- Fiscal years: "FY2024", "Fiscal 2024"
- Relative: "YTD", "TTM", "Last quarter"
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum


class DateGranularity(Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    HALF_YEAR = "half_year"
    YEAR = "year"
    FISCAL_YEAR = "fiscal_year"


@dataclass
class NormalizedDate:
    """A normalized financial date with range and granularity."""
    
    start_date: datetime
    end_date: datetime
    granularity: DateGranularity
    original_text: str
    fiscal_year_end_month: int = 12  # Default to calendar year
    
    def __str__(self) -> str:
        if self.granularity == DateGranularity.DAY:
            return self.start_date.strftime("%Y-%m-%d")
        elif self.granularity == DateGranularity.QUARTER:
            q = (self.start_date.month - 1) // 3 + 1
            return f"Q{q} {self.start_date.year}"
        elif self.granularity == DateGranularity.YEAR:
            return str(self.start_date.year)
        else:
            return f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"
    
    def overlaps(self, other: 'NormalizedDate') -> bool:
        """Check if two date ranges overlap."""
        return self.start_date <= other.end_date and other.start_date <= self.end_date
    
    def contains_date(self, date: datetime) -> bool:
        """Check if a specific date falls within this range."""
        return self.start_date <= date <= self.end_date


class FinancialDateNormalizer:
    """
    Normalizes financial date references to standard format.
    
    Usage:
        normalizer = FinancialDateNormalizer()
        result = normalizer.parse("Q2 2024")
        # NormalizedDate(start=2024-04-01, end=2024-06-30, granularity=QUARTER)
    """
    
    MONTH_MAP = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    
    # Patterns ordered by specificity (most specific first)
    PATTERNS = [
        # Period expressions: "Three months ended March 29, 2025"
        (r'(?:three|3)\s*months?\s*ended\s+(\w+)\s+(\d{1,2})(?:,?\s*(\d{4}))?', 'period_quarter'),
        (r'(?:six|6)\s*months?\s*ended\s+(\w+)\s+(\d{1,2})(?:,?\s*(\d{4}))?', 'period_half'),
        (r'(?:nine|9)\s*months?\s*ended\s+(\w+)\s+(\d{1,2})(?:,?\s*(\d{4}))?', 'period_nine'),
        (r'(?:twelve|12)\s*months?\s*ended\s+(\w+)\s+(\d{1,2})(?:,?\s*(\d{4}))?', 'period_year'),
        (r'(?:year|fiscal\s*year)\s*ended\s+(\w+)\s+(\d{1,2})(?:,?\s*(\d{4}))?', 'period_fy'),
        
        # Quarter formats: "Q1 2024", "1Q24", "Q1'24", "First Quarter 2024"
        (r'Q([1-4])\s*[\'`]?(\d{2,4})', 'quarter'),
        (r'([1-4])Q[\'`]?(\d{2,4})', 'quarter_reverse'),
        (r'(?:first|1st)\s*quarter\s*(\d{4})', 'quarter_word_1'),
        (r'(?:second|2nd)\s*quarter\s*(\d{4})', 'quarter_word_2'),
        (r'(?:third|3rd)\s*quarter\s*(\d{4})', 'quarter_word_3'),
        (r'(?:fourth|4th)\s*quarter\s*(\d{4})', 'quarter_word_4'),
        
        # Fiscal year: "FY2024", "FY24", "Fiscal 2024", "Fiscal Year 2024"
        (r'FY\s*[\'`]?(\d{2,4})', 'fiscal_year'),
        (r'fiscal\s*(?:year)?\s*[\'`]?(\d{4})', 'fiscal_year'),
        
        # Full dates: "March 29, 2025", "Mar 29 2025", "29 March 2025"
        (r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})', 'date_mdy'),
        (r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+),?\s*(\d{4})', 'date_dmy'),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', 'date_iso'),
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', 'date_numeric'),
        
        # Partial dates (will use current/inferred year): "Mar 29", "March 29"
        (r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?!\s*,?\s*\d)', 'date_partial'),
        
        # Month only: "March 2024", "Mar 2024"
        (r'(\w+)\s+(\d{4})', 'month_year'),
        
        # Year only: "2024", "2025"
        (r'\b(20\d{2})\b', 'year_only'),
        
        # Relative: "YTD", "TTM", "LTM"
        (r'\bYTD\b', 'ytd'),
        (r'\b(?:TTM|LTM)\b', 'ttm'),
    ]
    
    def __init__(self, default_year: int = None, fiscal_year_end_month: int = 12):
        """
        Initialize normalizer.
        
        Args:
            default_year: Year to use for partial dates (defaults to current year)
            fiscal_year_end_month: Month when fiscal year ends (1-12, default 12 = Dec)
        """
        self.default_year = default_year or datetime.now().year
        self.fiscal_year_end_month = fiscal_year_end_month
    
    def parse(self, text: str) -> Optional[NormalizedDate]:
        """
        Parse a date string and return normalized date range.
        
        Args:
            text: Date string to parse
            
        Returns:
            NormalizedDate or None if parsing fails
        """
        if not text or not isinstance(text, str):
            return None
            
        text_clean = text.strip().lower()
        
        for pattern, pattern_type in self.PATTERNS:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                try:
                    return self._process_match(match, pattern_type, text)
                except (ValueError, KeyError):
                    continue
        
        return None
    
    def extract_all_dates(self, text: str) -> List[NormalizedDate]:
        """Extract all date references from a text string."""
        dates = []
        text_clean = text.lower()
        
        for pattern, pattern_type in self.PATTERNS:
            for match in re.finditer(pattern, text_clean, re.IGNORECASE):
                try:
                    result = self._process_match(match, pattern_type, match.group(0))
                    if result:
                        dates.append(result)
                except (ValueError, KeyError):
                    continue
        
        # Remove duplicates based on date range
        unique_dates = []
        for d in dates:
            is_dup = False
            for ud in unique_dates:
                if d.start_date == ud.start_date and d.end_date == ud.end_date:
                    is_dup = True
                    break
            if not is_dup:
                unique_dates.append(d)
        
        return sorted(unique_dates, key=lambda x: x.start_date)
    
    def _process_match(self, match, pattern_type: str, original_text: str) -> Optional[NormalizedDate]:
        """Process a regex match and return a NormalizedDate."""
        
        if pattern_type == 'quarter':
            q, year = int(match.group(1)), self._normalize_year(match.group(2))
            return self._make_quarter(q, year, original_text)
        
        elif pattern_type == 'quarter_reverse':
            q, year = int(match.group(1)), self._normalize_year(match.group(2))
            return self._make_quarter(q, year, original_text)
        
        elif pattern_type.startswith('quarter_word_'):
            q = int(pattern_type[-1])
            year = int(match.group(1))
            return self._make_quarter(q, year, original_text)
        
        elif pattern_type == 'fiscal_year':
            year = self._normalize_year(match.group(1))
            return self._make_fiscal_year(year, original_text)
        
        elif pattern_type == 'date_mdy':
            month_str, day, year = match.group(1), int(match.group(2)), int(match.group(3))
            month = self._parse_month(month_str)
            if month:
                return self._make_day(year, month, day, original_text)
        
        elif pattern_type == 'date_dmy':
            day, month_str, year = int(match.group(1)), match.group(2), int(match.group(3))
            month = self._parse_month(month_str)
            if month:
                return self._make_day(year, month, day, original_text)
        
        elif pattern_type == 'date_iso':
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return self._make_day(year, month, day, original_text)
        
        elif pattern_type == 'date_numeric':
            m, d, y = int(match.group(1)), int(match.group(2)), self._normalize_year(match.group(3))
            return self._make_day(y, m, d, original_text)
        
        elif pattern_type == 'date_partial':
            month_str, day = match.group(1), int(match.group(2))
            month = self._parse_month(month_str)
            if month:
                return self._make_day(self.default_year, month, day, original_text)
        
        elif pattern_type == 'month_year':
            month_str, year = match.group(1), int(match.group(2))
            month = self._parse_month(month_str)
            if month:
                return self._make_month(year, month, original_text)
        
        elif pattern_type == 'year_only':
            year = int(match.group(1))
            return self._make_calendar_year(year, original_text)
        
        elif pattern_type.startswith('period_'):
            month_str, day = match.group(1), int(match.group(2))
            year = int(match.group(3)) if match.group(3) else self.default_year
            month = self._parse_month(month_str)
            if month:
                end_date = datetime(year, month, day)
                
                if 'quarter' in pattern_type:
                    start_date = end_date - timedelta(days=90)
                elif 'half' in pattern_type:
                    start_date = end_date - timedelta(days=180)
                elif 'nine' in pattern_type:
                    start_date = end_date - timedelta(days=270)
                else:  # year or fy
                    start_date = end_date - timedelta(days=365)
                
                return NormalizedDate(
                    start_date=start_date,
                    end_date=end_date,
                    granularity=DateGranularity.QUARTER if 'quarter' in pattern_type else DateGranularity.YEAR,
                    original_text=original_text
                )
        
        elif pattern_type == 'ytd':
            now = datetime.now()
            return NormalizedDate(
                start_date=datetime(now.year, 1, 1),
                end_date=now,
                granularity=DateGranularity.YEAR,
                original_text=original_text
            )
        
        elif pattern_type == 'ttm':
            now = datetime.now()
            return NormalizedDate(
                start_date=now - timedelta(days=365),
                end_date=now,
                granularity=DateGranularity.YEAR,
                original_text=original_text
            )
        
        return None
    
    def _parse_month(self, month_str: str) -> Optional[int]:
        """Parse month name to number."""
        return self.MONTH_MAP.get(month_str.lower().strip())
    
    def _normalize_year(self, year_str: str) -> int:
        """Normalize 2-digit years to 4-digit."""
        year = int(year_str)
        if year < 100:
            year = 2000 + year if year < 50 else 1900 + year
        return year
    
    def _make_quarter(self, q: int, year: int, original: str) -> NormalizedDate:
        """Create a quarter date range."""
        start_month = (q - 1) * 3 + 1
        end_month = q * 3
        
        start = datetime(year, start_month, 1)
        # Last day of end month
        if end_month == 12:
            end = datetime(year, 12, 31)
        else:
            end = datetime(year, end_month + 1, 1) - timedelta(days=1)
        
        return NormalizedDate(
            start_date=start,
            end_date=end,
            granularity=DateGranularity.QUARTER,
            original_text=original
        )
    
    def _make_fiscal_year(self, year: int, original: str) -> NormalizedDate:
        """Create a fiscal year date range."""
        # Fiscal year ending in the specified year
        if self.fiscal_year_end_month == 12:
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
        else:
            # E.g., FY2024 ending in September means Oct 2023 - Sep 2024
            start = datetime(year - 1, self.fiscal_year_end_month + 1, 1)
            end = datetime(year, self.fiscal_year_end_month + 1, 1) - timedelta(days=1)
        
        return NormalizedDate(
            start_date=start,
            end_date=end,
            granularity=DateGranularity.FISCAL_YEAR,
            original_text=original,
            fiscal_year_end_month=self.fiscal_year_end_month
        )
    
    def _make_calendar_year(self, year: int, original: str) -> NormalizedDate:
        """Create a calendar year date range."""
        return NormalizedDate(
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31),
            granularity=DateGranularity.YEAR,
            original_text=original
        )
    
    def _make_month(self, year: int, month: int, original: str) -> NormalizedDate:
        """Create a month date range."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year, 12, 31)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        return NormalizedDate(
            start_date=start,
            end_date=end,
            granularity=DateGranularity.MONTH,
            original_text=original
        )
    
    def _make_day(self, year: int, month: int, day: int, original: str) -> NormalizedDate:
        """Create a single day date range."""
        date = datetime(year, month, day)
        return NormalizedDate(
            start_date=date,
            end_date=date,
            granularity=DateGranularity.DAY,
            original_text=original
        )


# Convenience function
def normalize_date(text: str, default_year: int = None) -> Optional[NormalizedDate]:
    """Quick helper to normalize a date string."""
    return FinancialDateNormalizer(default_year=default_year).parse(text)


def extract_dates_from_text(text: str) -> List[NormalizedDate]:
    """Extract all date references from text."""
    return FinancialDateNormalizer().extract_all_dates(text)
