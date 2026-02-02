"""
Metrics Engine - Detects anomalies and computes competitive deltas.
"""

import pandas as pd


class MetricsEngine:
    """Analyzes Snowflake metrics for anomalies and competitive gaps."""

    # Metrics to monitor
    METRICS = ['PRODUCT_REVENUE_M', 'TOTAL_REVENUE_M', 'RPO_M', 'NRR_PERCENT',
               'CUSTOMERS_1M_PLUS', 'FCF_IN_MILLIONS', 'GROSS_MARGIN_PERCENT']

    def __init__(self, snowflake_metrics: pd.DataFrame, peer_financials: pd.DataFrame):
        self.snow_df = snowflake_metrics.sort_values('PERIOD_END_DATE', ascending=False)
        self.peer_df = peer_financials
        self.anomalies = []
        self.competitive_gaps = []

    def run_analysis(self):
        """Run all anomaly detection and return results."""
        self._detect_anomalies()
        self._detect_nrr_decline()
        self._detect_competitive_gaps()
        return {
            'anomalies': self.anomalies,
            'competitive_gaps': self.competitive_gaps
        }

    def _detect_anomalies(self):
        """Flag metrics that deviate >20% from 4-quarter moving average."""
        if len(self.snow_df) < 5:
            return

        current = self.snow_df.iloc[0]
        quarter = f"Q{current['FISCAL_QUARTER']} FY{current['FISCAL_YEAR']}"

        for col in self.METRICS:
            if col not in self.snow_df.columns:
                continue

            current_val = current[col]
            moving_avg = self.snow_df.iloc[1:5][col].mean()

            if pd.isna(current_val) or pd.isna(moving_avg) or moving_avg == 0:
                continue

            deviation = (current_val - moving_avg) / abs(moving_avg)

            # Flag if >20% below average (negative deviation on growth metrics)
            if deviation < -0.20:
                self.anomalies.append({
                    'metric': col.replace('_', ' ').title(),
                    'current': current_val,
                    'moving_avg': round(moving_avg, 1),
                    'deviation_pct': round(deviation * 100, 1),
                    'threat': 'HIGH' if deviation < -0.30 else 'MEDIUM',
                    'description': f"{col.replace('_', ' ').title()} is {abs(deviation)*100:.0f}% below 4Q average",
                    'quarter': quarter,
                    'source_bucket': 1
                })

    def _detect_nrr_decline(self):
        """Flag if NRR declining for 3+ consecutive quarters."""
        if 'NRR_PERCENT' not in self.snow_df.columns or len(self.snow_df) < 4:
            return

        nrr = self.snow_df['NRR_PERCENT'].head(4).tolist()
        if any(pd.isna(v) for v in nrr):
            return

        # Check for consistent decline
        declining = all(nrr[i] < nrr[i+1] for i in range(3))
        if declining:
            current = self.snow_df.iloc[0]
            self.anomalies.append({
                'metric': 'Net Revenue Retention',
                'current': nrr[0],
                'moving_avg': nrr[3],
                'deviation_pct': round((nrr[0] - nrr[3]) / nrr[3] * 100, 1),
                'threat': 'HIGH',
                'description': f"NRR declining for 4 quarters: {nrr[3]}% → {nrr[0]}%",
                'quarter': f"Q{current['FISCAL_QUARTER']} FY{current['FISCAL_YEAR']}",
                'source_bucket': 1
            })

    def _detect_competitive_gaps(self):
        """Compare Snowflake growth vs major cloud competitors."""
        if len(self.snow_df) < 5:
            return

        # Snowflake YoY product revenue growth
        snow_current = self.snow_df.iloc[0]['PRODUCT_REVENUE_M']
        snow_yoy = self.snow_df.iloc[4]['PRODUCT_REVENUE_M']
        if pd.isna(snow_current) or pd.isna(snow_yoy) or snow_yoy == 0:
            return
        snow_growth = (snow_current - snow_yoy) / snow_yoy * 100

        # Check cloud competitors
        for comp_id, metric_name in [('GOOGL', 'CLOUD_REVENUE'), ('AMZN', 'AWS_REVENUE')]:
            comp_data = self.peer_df[
                (self.peer_df['COMPANY_ID'] == comp_id) &
                (self.peer_df['METRIC_NAME'] == metric_name)
            ].sort_values('PERIOD_END_DATE', ascending=False)

            if len(comp_data) < 5:
                continue

            comp_current = comp_data.iloc[0]['METRIC_VALUE']
            comp_yoy = comp_data.iloc[4]['METRIC_VALUE']
            if comp_yoy == 0:
                continue
            comp_growth = (comp_current - comp_yoy) / comp_yoy * 100

            gap = snow_growth - comp_growth
            self.competitive_gaps.append({
                'competitor': comp_id,
                'snow_growth': round(snow_growth, 1),
                'comp_growth': round(comp_growth, 1),
                'gap': round(gap, 1),
                'advantage': gap > 0
            })

    def get_latest_kpis(self) -> dict:
        """Get formatted KPIs for the latest quarter."""
        if self.snow_df.empty:
            return {}

        q = self.snow_df.iloc[0]
        return {
            'Product Revenue': f"${q['PRODUCT_REVENUE_M']:.0f}M",
            'Total Revenue': f"${q['TOTAL_REVENUE_M']:.0f}M",
            'RPO': f"${q['RPO_M']:.0f}M",
            'NRR': f"{q['NRR_PERCENT']:.0f}%",
            '$1M+ Customers': f"{int(q['CUSTOMERS_1M_PLUS']):,}",
            'FCF': f"${q['FCF_IN_MILLIONS']:.1f}M",
            'Gross Margin': f"{q['GROSS_MARGIN_PERCENT']:.0f}%",
            'Quarter': f"Q{q['FISCAL_QUARTER']} FY{q['FISCAL_YEAR']}"
        }
