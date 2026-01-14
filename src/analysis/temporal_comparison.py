# src/analysis/temporal_comparison.py
"""
Temporal Comparison Engine
Handles year-over-year, quarter-over-quarter, and other time-based comparisons.

Critical for queries like:
- "Operating income for Greater China Q2 2024 vs Q2 2025?"
- "How did revenue change year-over-year?"
- "Compare all segments Q1 vs Q2"
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dateutil import parser
from src.analysis.metric_registry import METRIC_REGISTRY


# Temporal comparison trigger keywords
TEMPORAL_TRIGGERS = [
    "year-over-year", "yoy", "y-o-y", "year over year",
    "quarter-over-quarter", "qoq", "q-o-q", "quarter over quarter",
    "period-over-period", "pop", "period over period",
    "vs", "versus", "compared to", "change from",
    "same period", "prior year", "last year", "previous quarter",
    "three months ended", "six months ended", "fiscal year"
]


def is_temporal_comparison(query: str) -> bool:
    """
    Detect if query requires temporal comparison (same metric across different time periods).
    
    Examples:
    - "Operating income Q2 2024 vs Q2 2025" -> True
    - "Revenue for March 2024 and March 2025" -> True
    - "Year-over-year growth" -> True
    - "Compare revenue across all files" -> False (cross-document, not temporal)
    """
    q = query.lower()
    
    # Check for temporal triggers - these are strong indicators
    has_temporal_trigger = any(trigger in q for trigger in TEMPORAL_TRIGGERS)
    
    # If we have a strong temporal trigger, that's enough
    if has_temporal_trigger:
        return True
    
    # Otherwise, check for multiple year/date references
    years = re.findall(r'20\d{2}', q)
    has_multiple_years = len(set(years)) >= 2
    
    # Check for specific period references
    has_period_refs = bool(re.search(r'(q[1-4]|quarter|march|june|september|december|fiscal|three months|six months)', q, re.IGNORECASE))
    
    return has_multiple_years and has_period_refs


def extract_periods_from_query(query: str) -> List[Dict[str, Any]]:
    """
    Extract specific time periods mentioned in the query.
    
    Returns list of period dicts with 'text', 'year', 'quarter', 'month', etc.
    
    Examples:
    - "Q2 2024 vs Q2 2025" -> [{'text': 'Q2 2024', 'year': 2024, 'quarter': 2}, ...]
    - "March 30, 2024 and March 29, 2025" -> [{'text': 'March 30, 2024', ...}, ...]
    - "three months ended March 30, 2024" -> [{'text': 'March 30, 2024', ...}, ...]
    """
    periods = []
    
    # Pattern 1: "Q1 2024", "Q2 2025", etc.
    quarter_matches = re.finditer(r'q([1-4])\s+(\d{4})', query, re.IGNORECASE)
    for match in quarter_matches:
        periods.append({
            'text': match.group(0),
            'year': int(match.group(2)),
            'quarter': int(match.group(1)),
            'type': 'quarter'
        })
    
    # Pattern 2: Extract years first, then look for dates with those years
    years_in_query = list(set(re.findall(r'20\d{2}', query)))
    
    # Pattern 3: "three months ended March 30, 2024" - extract the date part
    # Also handles: "March 30, 2024", "March 2024", etc.
    for year in years_in_query:
        # Look for date patterns containing this year
        # Pattern: Month Day, Year or Month Year
        date_patterns = [
            # "March 30, 2024" or "March 29, 2025"
            rf'((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{{1,2}},?\s+{year})',
            # "Mar 30, 2024"
            rf'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{{1,2}},?\s+{year})',
            # "March 2024"
            rf'((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+{year})',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(1)
                    parsed_date = parser.parse(date_str, fuzzy=True)
                    
                    period_dict = {
                        'text': date_str,
                        'year': parsed_date.year,
                        'month': parsed_date.month,
                        'quarter': (parsed_date.month - 1) // 3 + 1,
                        'type': 'date',
                        'date_obj': parsed_date
                    }
                    
                    # Avoid duplicates
                    if not any(p.get('text') == date_str for p in periods):
                        periods.append(period_dict)
                except Exception as e:
                    print(f"⚠️ Error parsing date '{date_str}': {e}")
                    continue
    
    # Pattern 4: If still no periods but we have years and it's YoY query
    if not periods and len(years_in_query) >= 2:
        for year_str in sorted(years_in_query):
            periods.append({
                'text': year_str,
                'year': int(year_str),
                'type': 'year'
            })
    
    # Sort by year (oldest first for prior/current ordering)
    periods.sort(key=lambda p: (p['year'], p.get('quarter', 0), p.get('month', 0)))
    
    print(f"🔍 [PERIOD EXTRACT] Found {len(periods)} periods: {[p.get('text') for p in periods]}")
    
    return periods


def extract_metric_from_temporal_query(query: str) -> Optional[str]:
    """
    Identify which metric to compare using METRIC_REGISTRY.
    Prioritizes longest keyword matches.
    """
    query_lower = query.lower()
    
    matches = []
    for metric, config in METRIC_REGISTRY.items():
        for kw in config["keywords"]:
            if kw in query_lower:
                matches.append((metric, len(kw)))
    
    if matches:
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0]
    
    return None


def find_matching_columns(df: pd.DataFrame, period_info: Dict) -> List[str]:
    """
    Find column(s) in DataFrame that match the given period.
    
    Args:
        df: The DataFrame to search
        period_info: Dict with 'year', 'quarter', 'month', etc.
    
    Returns:
        List of matching column names
    """
    matching_cols = []
    year = period_info.get('year')
    quarter = period_info.get('quarter')
    month = period_info.get('month')
    
    for col in df.columns:
        col_str = str(col).lower()
        
        # Check for year match
        if year and str(year) in col_str:
            # If we have quarter info, check for that too
            if quarter:
                if f'q{quarter}' in col_str or f'quarter {quarter}' in col_str:
                    matching_cols.append(col)
                # Also check for month-based quarter matching
                elif month:
                    # Extract month from column if possible
                    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                                   'july', 'august', 'september', 'october', 'november', 'december']
                    month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                    
                    # Check if column contains the target month
                    target_month_name = month_names[month - 1]
                    target_month_abbr = month_abbr[month - 1]
                    
                    if target_month_name in col_str or target_month_abbr in col_str:
                        matching_cols.append(col)
            else:
                # No quarter specified, just year match is enough
                matching_cols.append(col)
    
    return matching_cols


def extract_multi_period_metric(
    metric_name: str,
    segment: Optional[str],
    tables: List[Dict],
    periods: List[Dict]
) -> Dict[str, Any]:
    """
    Extract the same metric across multiple time periods.
    
    This is the core function for temporal comparisons.
    
    Args:
        metric_name: The metric to extract (e.g., 'operating_income')
        segment: Optional segment filter (e.g., 'Greater China')
        tables: List of table dicts
        periods: List of period dicts from extract_periods_from_query()
    
    Returns:
        Dict with 'success', 'results' (list of period results), 'summary'
    """
    print(f"\n🕐 [TEMPORAL] Extracting {metric_name} for {len(periods)} periods")
    if segment:
        print(f"   Segment Filter: {segment}")
    
    # Get metric config
    metric_config = METRIC_REGISTRY.get(metric_name, {})
    keywords = metric_config.get('keywords', [])
    
    results = []
    
    for period in periods:
        print(f"\n   Period: {period.get('text', period)}")
        
        # Search through tables for matching data
        for table in tables:
            df = table.get('df')
            if df is None or df.empty:
                continue
            
            # Find columns matching this period
            matching_cols = find_matching_columns(df, period)
            
            if not matching_cols:
                continue
            
            print(f"      Found {len(matching_cols)} matching columns: {matching_cols}")
            
            # Search for the metric in the first column (row labels)
            first_col = df.iloc[:, 0].astype(str).str.lower()
            
            # CASE 1: Segment filter specified
            if segment:
                segment_mask = first_col.str.contains(segment.lower(), case=False, na=False)
                
                # First try: Segment + Metric in same row
                for kw in keywords:
                    metric_mask = first_col.str.contains(kw, case=False, na=False, regex=False)
                    combined_mask = metric_mask & segment_mask
                    
                    if combined_mask.any():
                        matching_rows = df[combined_mask]
                        for col in matching_cols:
                            try:
                                raw_value = matching_rows[col].iloc[0]
                                if isinstance(raw_value, str):
                                    clean_val = raw_value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                                    value = float(clean_val)
                                else:
                                    value = float(raw_value)
                                
                                results.append({
                                    'period': period.get('text', str(period)),
                                    'period_info': period,
                                    'value': value,
                                    'source': table.get('source', 'Unknown'),
                                    'page': table.get('page', '?'),
                                    'column': col,
                                    'row_label': matching_rows.iloc[0, 0],
                                    'segment': segment
                                })
                                print(f"      ✅ Extracted: {value} from column '{col}'")
                                break
                            except Exception as e:
                                print(f"      ⚠️ Error: {e}")
                                continue
                        if results and results[-1]['period'] == period.get('text', str(period)):
                            break
                
                # Second try: Segment-only table (segment name in first column, values in other columns)
                # This handles tables like: "Greater China" | 16,002 | 15,002
                if not results or results[-1]['period'] != period.get('text', str(period)):
                    if segment_mask.any():
                        matching_rows = df[segment_mask]
                        for col in matching_cols:
                            try:
                                raw_value = matching_rows[col].iloc[0]
                                if isinstance(raw_value, str):
                                    clean_val = raw_value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                                    if not clean_val or clean_val == '-':
                                        continue
                                    value = float(clean_val)
                                else:
                                    value = float(raw_value)
                                
                                results.append({
                                    'period': period.get('text', str(period)),
                                    'period_info': period,
                                    'value': value,
                                    'source': table.get('source', 'Unknown'),
                                    'page': table.get('page', '?'),
                                    'column': col,
                                    'row_label': matching_rows.iloc[0, 0],
                                    'segment': segment
                                })
                                print(f"      ✅ Extracted (segment-only): {value} from column '{col}'")
                                break
                            except Exception as e:
                                print(f"      ⚠️ Error: {e}")
                                continue
                        if results and results[-1]['period'] == period.get('text', str(period)):
                            break
            
            # CASE 2: No segment filter - just look for metric
            else:
                for kw in keywords:
                    metric_mask = first_col.str.contains(kw, case=False, na=False, regex=False)
                    
                    if metric_mask.any():
                        matching_rows = df[metric_mask]
                        for col in matching_cols:
                            try:
                                raw_value = matching_rows[col].iloc[0]
                                if isinstance(raw_value, str):
                                    clean_val = raw_value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                                    value = float(clean_val)
                                else:
                                    value = float(raw_value)
                                
                                results.append({
                                    'period': period.get('text', str(period)),
                                    'period_info': period,
                                    'value': value,
                                    'source': table.get('source', 'Unknown'),
                                    'page': table.get('page', '?'),
                                    'column': col,
                                    'row_label': matching_rows.iloc[0, 0],
                                    'segment': segment
                                })
                                print(f"      ✅ Extracted: {value} from column '{col}'")
                                break
                            except Exception as e:
                                print(f"      ⚠️ Error: {e}")
                                continue
                        if results and results[-1]['period'] == period.get('text', str(period)):
                            break
            
            # If we found data for this period, move to next period
            if results and results[-1]['period'] == period.get('text', str(period)):
                break
    
    if len(results) < len(periods):
        missing_periods = [p.get('text', str(p)) for p in periods 
                          if p.get('text', str(p)) not in [r['period'] for r in results]]
        print(f"\n   ⚠️ Could not extract data for periods: {missing_periods}")
    
    if len(results) < 2:
        return {
            'success': False,
            'error': f'Could only extract {metric_name} for {len(results)} period(s). Need at least 2 for comparison.',
            'results': results
        }
    
    # Calculate variances
    variance_data = calculate_temporal_variance(results)
    
    # Generate summary
    summary = generate_temporal_summary(metric_name, segment, results, variance_data)
    
    return {
        'success': True,
        'metric': metric_name,
        'segment': segment,
        'results': results,
        'variance': variance_data,
        'summary': summary,
        'period_count': len(results)
    }


def calculate_temporal_variance(results: List[Dict]) -> Dict[str, Any]:
    """
    Calculate variance between periods (typically current vs prior).
    
    Assumes results are sorted chronologically (oldest first).
    """
    if len(results) < 2:
        return {}
    
    # Assume last is current, second-to-last is prior
    prior = results[-2]
    current = results[-1]
    
    prior_val = prior['value']
    current_val = current['value']
    
    absolute_change = current_val - prior_val
    
    if prior_val != 0:
        percent_change = (absolute_change / abs(prior_val)) * 100
    else:
        percent_change = None
    
    return {
        'prior_value': prior_val,
        'current_value': current_val,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'prior_period': prior['period'],
        'current_period': current['period'],
        'direction': 'increase' if absolute_change > 0 else 'decrease' if absolute_change < 0 else 'flat'
    }


def generate_temporal_summary(
    metric_name: str,
    segment: Optional[str],
    results: List[Dict],
    variance: Dict
) -> str:
    """
    Generate human-readable summary of temporal comparison.
    """
    metric_display = metric_name.replace('_', ' ').title()
    segment_display = f" for {segment}" if segment else ""
    
    lines = [f"## Temporal Comparison: {metric_display}{segment_display}\n"]
    
    # Show all periods
    lines.append("### Period Breakdown\n")
    for i, res in enumerate(results, 1):
        value = res['value']
        # Format value
        metric_config = METRIC_REGISTRY.get(metric_name, {})
        unit_type = metric_config.get('unit', 'currency')
        
        if unit_type == 'percent':
            formatted = f"{value:.2f}%"
        elif unit_type == 'ratio':
            formatted = f"{value:.2f}x"
        else:
            # Currency
            if abs(value) >= 1_000_000_000:
                formatted = f"${value/1_000_000_000:.2f}B"
            elif abs(value) >= 1_000_000:
                formatted = f"${value/1_000_000:.2f}M"
            else:
                formatted = f"${value:,.2f}"
        
        lines.append(f"{i}. **{res['period']}**: {formatted}")
        lines.append(f"   - Source: {res['source']} (Page {res['page']})")
    
    # Variance analysis
    if variance:
        lines.append("\n### Variance Analysis\n")
        
        abs_change = variance['absolute_change']
        pct_change = variance.get('percent_change')
        direction = variance['direction']
        
        # Format absolute change
        if unit_type == 'percent':
            abs_formatted = f"{abs(abs_change):.2f} percentage points"
        elif unit_type == 'ratio':
            abs_formatted = f"{abs(abs_change):.2f}x"
        else:
            if abs(abs_change) >= 1_000_000_000:
                abs_formatted = f"${abs(abs_change)/1_000_000_000:.2f}B"
            elif abs(abs_change) >= 1_000_000:
                abs_formatted = f"${abs(abs_change)/1_000_000:.2f}M"
            else:
                abs_formatted = f"${abs(abs_change):,.2f}"
        
        direction_word = "**increased**" if direction == 'increase' else "**decreased**" if direction == 'decrease' else "remained flat"
        
        lines.append(f"- {metric_display} {direction_word} by {abs_formatted}")
        
        if pct_change is not None:
            lines.append(f"- Percentage Change: **{pct_change:+.2f}%**")
        
        lines.append(f"- From {variance['prior_period']} to {variance['current_period']}")
    
    # Try to get CFO insights
    try:
        from src.analysis.cfo_insights import CFOInsights
        if variance and variance.get('prior_value') and variance.get('current_value'):
            cfo = CFOInsights()
            cfo_commentary = cfo.generate_cfo_commentary(
                metric_name=metric_name,
                segment=segment or "Company",
                current_val=variance['current_value'],
                prior_val=variance['prior_value'],
                period_label=variance['current_period']
            )
            if cfo_commentary:
                lines.append(f"\n### 💼 CFO Strategic Advisory\n\n{cfo_commentary}")
    except Exception as e:
        print(f"⚠️ CFO insights generation failed: {e}")
    
    return "\n".join(lines)


def handle_temporal_comparison(query: str, tables: List[Dict]) -> Dict[str, Any]:
    """
    Main entry point for temporal comparison queries.
    
    Args:
        query: User query
        tables: List of table dicts
    
    Returns:
        Dict with 'success', 'summary', 'results', 'chart_data', etc.
    """
    # Detect periods
    periods = extract_periods_from_query(query)
    
    if len(periods) < 2:
        return {
            'success': False,
            'error': 'Could not identify at least 2 time periods in the query.',
            'is_temporal': True
        }
    
    print(f"🕐 [TEMPORAL] Detected {len(periods)} periods: {[p.get('text') for p in periods]}")
    
    # Detect metric
    metric = extract_metric_from_temporal_query(query)
    
    if not metric:
        return {
            'success': False,
            'error': 'Could not identify which metric to compare.',
            'is_temporal': True
        }
    
    print(f"📊 [TEMPORAL] Metric: {metric}")
    
    # Detect segment filter
    from src.analysis.question_router import detect_segment_filter
    segment = detect_segment_filter(query)
    
    # Extract data
    result = extract_multi_period_metric(metric, segment, tables, periods)
    
    if not result.get('success'):
        return result
    
    # Prepare chart data
    chart_data = pd.DataFrame({
        'Period': [r['period'] for r in result['results']],
        'Value': [r['value'] for r in result['results']]
    })
    
    result['chart_data'] = chart_data
    result['is_temporal'] = True
    
    return result
