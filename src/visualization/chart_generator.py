# src/visualization/chart_generator.py
"""
Production-grade chart generator using Plotly.
Generates beautiful, interactive charts suitable for financial reports.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
from pathlib import Path
import json

# ==========================================
# DATA SANITIZATION
# ==========================================

def sanitize_dataframe_for_charting(df: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    """
    Clean DataFrame for charting - handles string numbers, mixed types, etc.
    """
    from src.analysis.robust_value_extractor import extract_financial_value
    
    df = df.copy()
    
    # Clean y-axis (must be numeric)
    if not pd.api.types.is_numeric_dtype(df[y_col]):
        df[y_col] = df[y_col].apply(lambda x: extract_financial_value(x))
    
    # Clean x-axis (try datetime first, then keep as-is)
    if x_col and not pd.api.types.is_numeric_dtype(df[x_col]) and not pd.api.types.is_datetime64_any_dtype(df[x_col]):
        try:
            df[x_col] = pd.to_datetime(df[x_col], errors='coerce')
        except:
            pass  # Keep as categorical
    
    # Remove rows where y is null
    df = df.dropna(subset=[y_col])
    
    return df

# ==========================================
# SMART CHART TYPE DETECTION
# ==========================================

def detect_chart_type(df: pd.DataFrame, x_col: str, y_col: str) -> str:
    """
    Intelligently detect the best chart type based on data characteristics.
    """
    # Time series detection
    if is_time_series(df, x_col):
        return "line"
    
    # Composition (parts of whole) → Pie
    if is_categorical(df, x_col) and is_composition(df, y_col):
        return "pie"
    
    # Categorical comparison → Bar
    if is_categorical(df, x_col):
        return "bar"
    
    # Two numeric columns → Scatter
    if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        return "scatter"
    
    # Default
    return "bar"

def is_time_series(df: pd.DataFrame, col: str) -> bool:
    """Check if column contains time/date data."""
    try:
        if df[col].dtype == 'object':
            parsed = pd.to_datetime(df[col], errors='coerce')
            return parsed.notna().sum() > len(df) * 0.5
        return pd.api.types.is_datetime64_any_dtype(df[col])
    except:
        return False

def is_categorical(df: pd.DataFrame, col: str, threshold: int = 15) -> bool:
    """Check if column is categorical (low unique values)."""
    return df[col].nunique() <= threshold

def is_composition(df: pd.DataFrame, col: str) -> bool:
    """Check if data represents parts of a whole (sum ≈ 100 or 1)."""
    if pd.api.types.is_numeric_dtype(df[col]):
        total = df[col].sum()
        return abs(total - 100) < 5 or abs(total - 1.0) < 0.1
    return False

# ==========================================
# CHART GENERATORS (PLOTLY)
# ==========================================

def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create professional line chart for trends."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(color='#2E86DE', width=3),
        marker=dict(size=8, color='#2E86DE', line=dict(width=2, color='white'))
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white',
        hovermode='x unified',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.3)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.3)')
    )
    
    return fig

def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create professional bar chart for comparisons."""
    # Determine if values are positive/negative for coloring
    colors = ['#27AE60' if val >= 0 else '#E74C3C' for val in df[y_col]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df[x_col],
        y=df[y_col],
        marker=dict(
            color=colors,
            line=dict(color='white', width=2)
        ),
        text=df[y_col].apply(lambda x: f'{x:,.0f}' if abs(x) > 1000 else f'{x:.2f}'),
        textposition='outside',
        name=y_col
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)',
        showlegend=False
    )
    
    return fig

def create_pie_chart(df: pd.DataFrame, labels_col: str, values_col: str, title: str) -> go.Figure:
    """Create professional pie chart for composition."""
    fig = go.Figure()
    
    # Color palette (professional finance colors)
    colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6', '#1ABC9C', '#34495E', '#E67E22']
    
    fig.add_trace(go.Pie(
        labels=df[labels_col],
        values=df[values_col],
        hole=0.4,  # Donut chart
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textposition='outside',
        textinfo='label+percent',
        textfont=dict(size=12, family='Arial'),
        hovertemplate='<b>%{label}</b><br>Value: %{value:,.0f}<br>Percent: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        template='plotly_white',
        font=dict(family='Arial', size=12),
        showlegend=True,
        legend=dict(orientation='v', x=1.1, y=0.5)
    )
    
    return fig

def create_scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    """Create professional scatter plot for correlations."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='markers',
        marker=dict(
            size=12,
            color=df[y_col],
            colorscale='Viridis',
            showscale=True,
            line=dict(width=1, color='white')
        ),
        text=df.index,
        hovertemplate='<b>%{text}</b><br>%{x}: %{y:,.2f}<extra></extra>'
    ))
    
    # Add trend line
    if len(df) > 2:
        import numpy as np
        z = np.polyfit(df[x_col], df[y_col], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=p(df[x_col]),
            mode='lines',
            name='Trend',
            line=dict(color='red', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)'
    )
    
    return fig

# ==========================================
# WATERFALL CHART (Variance Analysis)
# ==========================================

def create_waterfall_chart(
    labels: list,
    values: list,
    title: str = "Variance Analysis"
) -> go.Figure:
    """
    Create professional waterfall chart for variance/bridge analysis.
    
    Args:
        labels: List of step labels (e.g., ['Q1 2024', 'Growth', 'Expenses', 'Q1 2025'])
        values: List of values (first and last are totals, middle are changes)
        title: Chart title
    """
    # Determine measure types (first=absolute, middle=relative, last=total)
    measures = []
    for i, val in enumerate(values):
        if i == 0:
            measures.append("absolute")  # Starting point
        elif i == len(values) - 1:
            measures.append("total")  # Ending point
        else:
            measures.append("relative")  # Changes
    
    # Colors: green for positive, red for negative
    colors = []
    for i, val in enumerate(values):
        if measures[i] == "absolute" or measures[i] == "total":
            colors.append("#3498DB")  # Blue for totals
        elif val >= 0:
            colors.append("#27AE60")  # Green for positive change
        else:
            colors.append("#E74C3C")  # Red for negative change
    
    fig = go.Figure(go.Waterfall(
        name="Variance",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        connector={"line": {"color": "#7F8C8D", "width": 2, "dash": "dot"}},
        decreasing={"marker": {"color": "#E74C3C"}},
        increasing={"marker": {"color": "#27AE60"}},
        totals={"marker": {"color": "#3498DB"}},
        text=[f"{v:+,.0f}" if i > 0 and i < len(values)-1 else f"{v:,.0f}" for i, v in enumerate(values)],
        textposition="outside",
        textfont=dict(size=12, family="Arial")
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        template='plotly_white',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)',
        showlegend=False,
        waterfallgap=0.3
    )
    
    return fig


def create_comparison_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    value_cols: list,
    title: str = "Comparison"
) -> go.Figure:
    """
    Create grouped bar chart for multi-period/multi-metric comparisons.
    
    Args:
        df: DataFrame with data
        x_col: Column for categories (x-axis)
        value_cols: List of value column names to compare
        title: Chart title
    """
    fig = go.Figure()
    
    # Color palette for multiple series
    colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
    
    for i, col in enumerate(value_cols):
        color = colors[i % len(colors)]
        fig.add_trace(go.Bar(
            name=col,
            x=df[x_col],
            y=df[col],
            marker_color=color,
            text=df[col].apply(lambda x: f'{x:,.0f}' if abs(x) > 1000 else f'{x:.2f}'),
            textposition='outside'
        ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        xaxis_title=x_col,
        yaxis_title="Value",
        barmode='group',
        template='plotly_white',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig


def create_trend_forecast_chart(
    historical_df: pd.DataFrame,
    x_col: str,
    y_col: str,
    forecast_df: pd.DataFrame = None,
    title: str = "Trend with Forecast"
) -> go.Figure:
    """
    Create line chart with historical data and optional forecast projection.
    """
    fig = go.Figure()
    
    # Historical data (solid line)
    fig.add_trace(go.Scatter(
        x=historical_df[x_col],
        y=historical_df[y_col],
        mode='lines+markers',
        name='Actual',
        line=dict(color='#2E86DE', width=3),
        marker=dict(size=8, color='#2E86DE')
    ))
    
    # Forecast data (dashed line)
    if forecast_df is not None and not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=forecast_df[x_col],
            y=forecast_df[y_col],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#E74C3C', width=2, dash='dash'),
            marker=dict(size=6, color='#E74C3C', symbol='diamond')
        ))
        
        # Add confidence band if available
        if 'lower_bound' in forecast_df.columns and 'upper_bound' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=list(forecast_df[x_col]) + list(forecast_df[x_col][::-1]),
                y=list(forecast_df['upper_bound']) + list(forecast_df['lower_bound'][::-1]),
                fill='toself',
                fillcolor='rgba(231,76,60,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='Confidence Band',
                showlegend=True
            ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color='#2C3E50', family='Arial Black')),
        xaxis_title=x_col,
        yaxis_title=y_col,
        template='plotly_white',
        font=dict(family='Arial', size=12),
        plot_bgcolor='rgba(240,240,240,0.5)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    return fig

# ==========================================
# MAIN GENERATOR FUNCTION
# ==========================================

def generate_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "Financial Data Visualization",
    output_path: Optional[str] = None,
    chart_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate publication-quality financial charts.
    
    Args:
        df: DataFrame with data
        x_col: Column for X-axis
        y_col: Column for Y-axis
        title: Chart title
        output_path: Path to save PNG (optional)
        chart_type: Force specific chart type (optional)
    
    Returns:
        Dictionary with chart metadata
    """
    # Clean data
    df = df.copy()
    df = df.dropna(subset=[x_col, y_col])
    
    if df.empty:
        return {"error": "No valid data after cleaning", "chart_type": None}
    
    # Auto-detect chart type if not specified
    if chart_type is None:
        chart_type = detect_chart_type(df, x_col, y_col)

    # ✅ SANITIZE DATA (Fixes TypeError: '>=' not supported between instances of 'str' and 'int')
    df = sanitize_dataframe_for_charting(df, x_col, y_col)
    
    # Generate chart
    try:
        if chart_type == "line":
            fig = create_line_chart(df, x_col, y_col, title)
        elif chart_type == "bar":
            fig = create_bar_chart(df, x_col, y_col, title)
        elif chart_type == "pie":
            fig = create_pie_chart(df, x_col, y_col, title)
        elif chart_type == "scatter":
            fig = create_scatter_chart(df, x_col, y_col, title)
        else:
            fig = create_bar_chart(df, x_col, y_col, title)  # Default fallback
        
        # Save as PNG if path provided
        image_path = None
        if output_path:
            try:
                fig.write_image(output_path, width=1200, height=700, scale=2)
                image_path = output_path
                print(f"✅ Chart saved: {output_path}")
            except Exception as e:
                print(f"⚠️ Could not save PNG (install kaleido: pip install kaleido): {e}")
                # Save as HTML fallback
                html_path = output_path.replace('.png', '.html')
                fig.write_html(html_path)
                image_path = html_path
                print(f"✅ Saved as interactive HTML: {html_path}")
        
        return {
            "chart_type": chart_type,
            "image_path": image_path,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Chart generation failed: {e}")
        return {"error": str(e), "chart_type": chart_type, "success": False}

# ==========================================
# FINANCIAL DASHBOARD GENERATOR
# ==========================================

def create_financial_dashboard(
    revenue_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    cash_df: pd.DataFrame,
    output_path: str
) -> str:
    """
    Create a complete financial dashboard with multiple charts.
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Revenue Trend', 'Expense Breakdown', 'Cash Flow', 'Key Metrics'),
        specs=[[{"type": "scatter"}, {"type": "pie"}],
               [{"type": "bar"}, {"type": "indicator"}]]
    )
    
    # Revenue trend (top-left)
    if not revenue_df.empty:
        fig.add_trace(
            go.Scatter(x=revenue_df.iloc[:, 0], y=revenue_df.iloc[:, 1], mode='lines+markers', name='Revenue'),
            row=1, col=1
        )
    
    # Expenses pie (top-right)
    if not expenses_df.empty:
        fig.add_trace(
            go.Pie(labels=expenses_df.iloc[:, 0], values=expenses_df.iloc[:, 1], name='Expenses'),
            row=1, col=2
        )
    
    # Cash flow bar (bottom-left)
    if not cash_df.empty:
        fig.add_trace(
            go.Bar(x=cash_df.iloc[:, 0], y=cash_df.iloc[:, 1], name='Cash'),
            row=2, col=1
        )
    
    fig.update_layout(height=800, showlegend=True, title_text="Financial Dashboard")
    fig.write_html(output_path)
    
    return output_path