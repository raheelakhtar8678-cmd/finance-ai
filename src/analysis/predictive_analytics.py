# src/analysis/predictive_analytics.py
"""
Predictive Analytics Module
Provides forecasting, trend analysis, and growth projections.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
from dataclasses import dataclass


@dataclass
class ForecastResult:
    """Result of a forecast calculation."""
    predicted_value: float
    confidence_level: str  # "high", "medium", "low"
    trend_direction: str  # "increasing", "decreasing", "stable"
    growth_rate: float
    method: str
    data_points_used: int


# ============================================================
# GROWTH RATE CALCULATIONS
# ============================================================

def calculate_growth_rate(current: float, prior: float) -> Dict[str, Any]:
    """
    Calculate simple growth rate between two periods.
    """
    if prior == 0:
        return {
            'success': False,
            'error': 'Prior value is zero, cannot calculate growth rate'
        }
    
    absolute_change = current - prior
    percent_change = ((current - prior) / abs(prior)) * 100
    
    return {
        'success': True,
        'absolute_change': absolute_change,
        'percent_change': percent_change,
        'direction': 'increase' if percent_change > 0 else 'decrease' if percent_change < 0 else 'flat',
        'current': current,
        'prior': prior
    }


def calculate_cagr(beginning_value: float, ending_value: float, years: float) -> Dict[str, Any]:
    """
    Calculate Compound Annual Growth Rate.
    
    CAGR = (Ending Value / Beginning Value)^(1/years) - 1
    """
    if beginning_value <= 0:
        return {
            'success': False,
            'error': 'Beginning value must be positive'
        }
    
    if years <= 0:
        return {
            'success': False,
            'error': 'Years must be positive'
        }
    
    cagr = (pow(ending_value / beginning_value, 1 / years) - 1) * 100
    
    return {
        'success': True,
        'cagr': cagr,
        'beginning_value': beginning_value,
        'ending_value': ending_value,
        'years': years,
        'formula': f"((({ending_value:,.0f} / {beginning_value:,.0f})^(1/{years:.1f})) - 1) × 100 = {cagr:.2f}%"
    }


def calculate_qoq_growth(values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate quarter-over-quarter growth rates for a series.
    
    Args:
        values: List of dicts with 'period' and 'value' keys, sorted chronologically
    """
    if len(values) < 2:
        return []
    
    results = []
    for i in range(1, len(values)):
        current = values[i]
        prior = values[i - 1]
        
        growth = calculate_growth_rate(current['value'], prior['value'])
        
        if growth['success']:
            results.append({
                'period': current['period'],
                'prior_period': prior['period'],
                'current_value': current['value'],
                'prior_value': prior['value'],
                'qoq_growth': growth['percent_change'],
                'direction': growth['direction']
            })
    
    return results


def calculate_yoy_growth(values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate year-over-year growth rates.
    Assumes values are quarterly and tries to match same quarter from prior year.
    """
    # Group by quarter
    by_quarter = {}
    for v in values:
        period = v.get('period', '')
        # Try to extract quarter identifier
        quarter = None
        if 'q1' in period.lower() or 'mar' in period.lower():
            quarter = 'Q1'
        elif 'q2' in period.lower() or 'jun' in period.lower():
            quarter = 'Q2'
        elif 'q3' in period.lower() or 'sep' in period.lower():
            quarter = 'Q3'
        elif 'q4' in period.lower() or 'dec' in period.lower():
            quarter = 'Q4'
        
        if quarter:
            if quarter not in by_quarter:
                by_quarter[quarter] = []
            by_quarter[quarter].append(v)
    
    results = []
    for quarter, quarter_values in by_quarter.items():
        if len(quarter_values) >= 2:
            # Sort by year (assuming year is in period string)
            sorted_vals = sorted(quarter_values, key=lambda x: x.get('period', ''))
            for i in range(1, len(sorted_vals)):
                growth = calculate_growth_rate(sorted_vals[i]['value'], sorted_vals[i-1]['value'])
                if growth['success']:
                    results.append({
                        'quarter': quarter,
                        'current_period': sorted_vals[i]['period'],
                        'prior_period': sorted_vals[i-1]['period'],
                        'yoy_growth': growth['percent_change'],
                        'direction': growth['direction']
                    })
    
    return results


# ============================================================
# TREND ANALYSIS
# ============================================================

def analyze_trend(values: List[float]) -> Dict[str, Any]:
    """
    Analyze the trend in a series of values using linear regression.
    
    Args:
        values: List of numeric values in chronological order
    
    Returns:
        Dict with trend direction, slope, strength, and forecast
    """
    if len(values) < 2:
        return {
            'success': False,
            'error': 'Need at least 2 data points for trend analysis'
        }
    
    n = len(values)
    x = list(range(n))
    
    # Calculate linear regression
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    
    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return {
            'success': True,
            'direction': 'stable',
            'slope': 0,
            'strength': 0,
            'data_points': n
        }
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R-squared for trend strength
    ss_tot = sum((v - y_mean) ** 2 for v in values)
    ss_res = sum((values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
    
    if ss_tot == 0:
        r_squared = 1.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    # Determine direction
    if slope > 0.01 * y_mean:  # Significant positive slope
        direction = 'increasing'
    elif slope < -0.01 * y_mean:  # Significant negative slope
        direction = 'decreasing'
    else:
        direction = 'stable'
    
    # Trend strength
    if r_squared > 0.8:
        strength = 'strong'
    elif r_squared > 0.5:
        strength = 'moderate'
    else:
        strength = 'weak'
    
    return {
        'success': True,
        'direction': direction,
        'slope': slope,
        'slope_per_period': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'strength': strength,
        'data_points': n,
        'first_value': values[0],
        'last_value': values[-1],
        'average': y_mean
    }


def detect_seasonality(quarterly_values: List[Dict]) -> Dict[str, Any]:
    """
    Detect seasonal patterns in quarterly data.
    
    Args:
        quarterly_values: List of dicts with 'quarter' (Q1-Q4) and 'value'
    """
    if len(quarterly_values) < 4:
        return {
            'success': False,
            'error': 'Need at least 4 quarters for seasonality detection',
            'has_seasonality': False
        }
    
    # Group by quarter
    by_quarter = {'Q1': [], 'Q2': [], 'Q3': [], 'Q4': []}
    
    for v in quarterly_values:
        q = v.get('quarter', '').upper()
        if q in by_quarter:
            by_quarter[q].append(v.get('value', 0))
    
    # Calculate average for each quarter
    quarter_averages = {}
    for q, vals in by_quarter.items():
        if vals:
            quarter_averages[q] = sum(vals) / len(vals)
    
    if len(quarter_averages) < 4:
        return {
            'success': True,
            'has_seasonality': False,
            'reason': 'Insufficient quarterly data'
        }
    
    # Calculate overall average
    all_values = [v for vals in by_quarter.values() for v in vals]
    overall_avg = sum(all_values) / len(all_values)
    
    # Determine seasonal indices
    seasonal_indices = {}
    for q, avg in quarter_averages.items():
        seasonal_indices[q] = avg / overall_avg if overall_avg else 1.0
    
    # Check if there's meaningful seasonality (any quarter differs by >10%)
    max_deviation = max(abs(idx - 1.0) for idx in seasonal_indices.values())
    has_seasonality = max_deviation > 0.10
    
    # Find peak and trough quarters
    peak_q = max(seasonal_indices.keys(), key=lambda k: seasonal_indices[k])
    trough_q = min(seasonal_indices.keys(), key=lambda k: seasonal_indices[k])
    
    return {
        'success': True,
        'has_seasonality': has_seasonality,
        'seasonal_indices': seasonal_indices,
        'peak_quarter': peak_q,
        'peak_index': seasonal_indices[peak_q],
        'trough_quarter': trough_q,
        'trough_index': seasonal_indices[trough_q],
        'seasonal_range': max_deviation * 100,
        'quarter_averages': quarter_averages
    }


# ============================================================
# FORECASTING
# ============================================================

def forecast_next_period(values: List[float], method: str = 'linear') -> Dict[str, Any]:
    """
    Forecast the next period's value based on historical data.
    
    Args:
        values: List of values in chronological order
        method: 'linear' (trend), 'average', or 'last' (naive)
    
    Returns:
        Dict with forecast value, confidence, and explanation
    """
    if not values:
        return {
            'success': False,
            'error': 'No values provided for forecasting'
        }
    
    n = len(values)
    
    if method == 'last' or n == 1:
        # Naive forecast: just use last value
        forecast = values[-1]
        confidence = 'low'
        explanation = "Naive forecast using most recent value"
        
    elif method == 'average':
        # Simple average
        forecast = sum(values) / n
        confidence = 'low' if n < 4 else 'medium'
        explanation = f"Average of last {n} periods"
        
    else:  # linear trend
        trend = analyze_trend(values)
        if not trend.get('success'):
            return trend
        
        # Forecast = intercept + slope * (next period index)
        forecast = trend['intercept'] + trend['slope'] * n
        
        # Confidence based on R-squared and data points
        if trend['r_squared'] > 0.8 and n >= 4:
            confidence = 'high'
        elif trend['r_squared'] > 0.5 and n >= 3:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        explanation = f"Linear trend projection (R² = {trend['r_squared']:.2f})"
    
    # Calculate simple forecast bounds (±10% for low, ±5% for high)
    if confidence == 'high':
        lower_bound = forecast * 0.95
        upper_bound = forecast * 1.05
    elif confidence == 'medium':
        lower_bound = forecast * 0.90
        upper_bound = forecast * 1.10
    else:
        lower_bound = forecast * 0.85
        upper_bound = forecast * 1.15
    
    return {
        'success': True,
        'forecast': forecast,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'confidence': confidence,
        'method': method,
        'explanation': explanation,
        'data_points_used': n,
        'last_actual': values[-1]
    }


def generate_multi_period_forecast(
    values: List[float], 
    periods_ahead: int = 4
) -> Dict[str, Any]:
    """
    Generate forecasts for multiple future periods.
    """
    if len(values) < 2:
        return {
            'success': False,
            'error': 'Need at least 2 data points for multi-period forecast'
        }
    
    trend = analyze_trend(values)
    if not trend.get('success'):
        return trend
    
    n = len(values)
    forecasts = []
    
    for i in range(1, periods_ahead + 1):
        forecast_value = trend['intercept'] + trend['slope'] * (n + i - 1)
        
        # Confidence decreases with distance
        if i <= 2:
            conf = 'medium' if trend['r_squared'] > 0.5 else 'low'
        else:
            conf = 'low'
        
        forecasts.append({
            'period_ahead': i,
            'forecast': forecast_value,
            'confidence': conf
        })
    
    return {
        'success': True,
        'forecasts': forecasts,
        'trend': trend,
        'total_forecast_growth': (forecasts[-1]['forecast'] - values[-1]) / values[-1] * 100 if values[-1] != 0 else 0
    }


# ============================================================
# PREDICTIVE INSIGHTS
# ============================================================

def generate_predictive_insights(
    metric_name: str,
    historical_values: List[Dict[str, Any]],
    segment: Optional[str] = None
) -> str:
    """
    Generate CFO-grade predictive insights based on historical data.
    
    Args:
        metric_name: Name of the metric being analyzed
        historical_values: List of dicts with 'period' and 'value'
        segment: Optional segment name
    
    Returns:
        Markdown-formatted insights string
    """
    if len(historical_values) < 2:
        return "⚠️ Insufficient historical data for predictive analysis."
    
    values = [v['value'] for v in historical_values]
    periods = [v['period'] for v in historical_values]
    
    lines = []
    metric_display = metric_name.replace('_', ' ').title()
    segment_text = f" for {segment}" if segment else ""
    
    lines.append(f"## 🔮 Predictive Analysis: {metric_display}{segment_text}\n")
    
    # 1. Trend Analysis
    trend = analyze_trend(values)
    if trend.get('success'):
        lines.append(f"### Trend Analysis\n")
        lines.append(f"- **Direction**: {trend['direction'].title()}")
        lines.append(f"- **Strength**: {trend['strength'].title()} (R² = {trend['r_squared']:.2f})")
        lines.append(f"- **Average Change per Period**: {trend['slope']:+,.2f}")
        lines.append("")
    
    # 2. Growth Rates
    if len(values) >= 2:
        latest_growth = calculate_growth_rate(values[-1], values[-2])
        if latest_growth.get('success'):
            lines.append(f"### Recent Growth\n")
            lines.append(f"- **Latest Period Change**: {latest_growth['percent_change']:+.2f}%")
            lines.append(f"- **Absolute Change**: {latest_growth['absolute_change']:+,.2f}")
            lines.append("")
    
    # 3. Forecast
    forecast = forecast_next_period(values, method='linear')
    if forecast.get('success'):
        lines.append(f"### Next Period Forecast\n")
        
        # Format forecast value
        fv = forecast['forecast']
        if abs(fv) >= 1_000_000_000:
            formatted = f"${fv/1_000_000_000:.2f}B"
        elif abs(fv) >= 1_000_000:
            formatted = f"${fv/1_000_000:.2f}M"
        else:
            formatted = f"${fv:,.2f}"
        
        lines.append(f"- **Projected Value**: {formatted}")
        lines.append(f"- **Confidence**: {forecast['confidence'].title()}")
        lines.append(f"- **Method**: {forecast['explanation']}")
        
        # Calculate projected change
        if values[-1] != 0:
            proj_change = ((forecast['forecast'] - values[-1]) / values[-1]) * 100
            lines.append(f"- **Projected Change**: {proj_change:+.2f}%")
        lines.append("")
    
    # 4. Strategic Implications
    lines.append(f"### 💼 Strategic Implications\n")
    
    if trend.get('direction') == 'increasing' and trend.get('strength') == 'strong':
        lines.append("- ✅ **Positive Momentum**: Strong upward trend suggests continued growth")
        lines.append("- Consider accelerating investment in this area")
    elif trend.get('direction') == 'decreasing' and trend.get('strength') == 'strong':
        lines.append("- ⚠️ **Concerning Decline**: Strong downward trend requires attention")
        lines.append("- Recommend root cause analysis and corrective action")
    elif trend.get('direction') == 'stable':
        lines.append("- 📊 **Stable Performance**: Consistent results over the period")
        lines.append("- Monitor for emerging trends and opportunities")
    else:
        lines.append("- 📈 **Mixed Signals**: Trend is not strongly pronounced")
        lines.append("- Continue monitoring for clearer directional signals")
    
    return "\n".join(lines)
