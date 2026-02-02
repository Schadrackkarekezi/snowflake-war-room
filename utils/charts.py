"""Plotly charts for the dashboard."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def revenue_trend_chart(snowflake_metrics: pd.DataFrame) -> go.Figure:
    """Create a revenue trend chart for Snowflake."""
    df = snowflake_metrics.sort_values('PERIOD_END_DATE')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['PERIOD_END_DATE'],
        y=df['PRODUCT_REVENUE_M'],
        mode='lines+markers',
        name='Product Revenue',
        line=dict(color='#29B5E8', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=df['PERIOD_END_DATE'],
        y=df['TOTAL_REVENUE_M'],
        mode='lines+markers',
        name='Total Revenue',
        line=dict(color='#FF6B6B', width=3)
    ))

    fig.update_layout(
        title='Snowflake Revenue Trend',
        xaxis_title='Quarter',
        yaxis_title='Revenue ($M)',
        template='plotly_dark',
        height=400
    )
    return fig


def nrr_trend_chart(snowflake_metrics: pd.DataFrame) -> go.Figure:
    """Create NRR trend chart."""
    df = snowflake_metrics.sort_values('PERIOD_END_DATE')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['PERIOD_END_DATE'],
        y=df['NRR_PERCENT'],
        mode='lines+markers',
        name='Net Revenue Retention',
        line=dict(color='#00D4AA', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 170, 0.1)'
    ))

    # Add 100% reference line
    fig.add_hline(y=100, line_dash="dash", line_color="gray",
                  annotation_text="100% baseline")

    fig.update_layout(
        title='Net Revenue Retention Trend',
        xaxis_title='Quarter',
        yaxis_title='NRR (%)',
        template='plotly_dark',
        height=400
    )
    return fig


def fcf_chart(snowflake_metrics: pd.DataFrame) -> go.Figure:
    """Create FCF trend chart."""
    df = snowflake_metrics.sort_values('PERIOD_END_DATE')

    colors = ['#00D4AA' if x >= 0 else '#FF6B6B' for x in df['FCF_IN_MILLIONS']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['PERIOD_END_DATE'],
        y=df['FCF_IN_MILLIONS'],
        marker_color=colors,
        name='Free Cash Flow'
    ))

    fig.update_layout(
        title='Free Cash Flow by Quarter',
        xaxis_title='Quarter',
        yaxis_title='FCF ($M)',
        template='plotly_dark',
        height=400
    )
    return fig


def competitive_growth_chart(snow_growth: float, competitors: list) -> go.Figure:
    """Create competitive growth comparison bar chart."""
    companies = ['Snowflake'] + [c['competitor'] for c in competitors]
    growth_rates = [snow_growth] + [c['comp_growth'] for c in competitors]

    colors = ['#29B5E8'] + ['#FF6B6B' if g > snow_growth else '#00D4AA' for g in growth_rates[1:]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=companies,
        y=growth_rates,
        marker_color=colors,
        text=[f'{g:.1f}%' for g in growth_rates],
        textposition='outside'
    ))

    fig.update_layout(
        title='YoY Revenue Growth Comparison',
        xaxis_title='Company',
        yaxis_title='Growth Rate (%)',
        template='plotly_dark',
        height=400,
        margin=dict(t=60, b=40),
        yaxis=dict(range=[0, max(growth_rates) * 1.2])
    )
    return fig


def customer_growth_chart(snowflake_metrics: pd.DataFrame) -> go.Figure:
    """Create $1M+ customer growth chart."""
    df = snowflake_metrics.sort_values('PERIOD_END_DATE')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['PERIOD_END_DATE'],
        y=df['CUSTOMERS_1M_PLUS'],
        marker_color='#29B5E8',
        text=df['CUSTOMERS_1M_PLUS'].astype(int),
        textposition='outside'
    ))

    fig.update_layout(
        title='$1M+ Customer Count',
        xaxis_title='Quarter',
        yaxis_title='Number of Customers',
        template='plotly_dark',
        height=400,
        margin=dict(t=60, b=40),
        yaxis=dict(range=[0, df['CUSTOMERS_1M_PLUS'].max() * 1.15])
    )
    return fig


def kpi_cards_data(kpis: dict) -> list:
    """Format KPIs for display as cards."""
    return [
        {'label': k, 'value': v}
        for k, v in kpis.items()
        if k != 'Quarter'
    ]
