"""Loads CSV data."""

import pandas as pd
from pathlib import Path


class DataLoader:
    """Loads CSV data for the War Room application."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data = {}

    def load_all(self) -> dict:
        """Load all CSV files and return as dictionary of DataFrames."""
        files = {
            'snowflake_metrics': 'snowflake_ir_metrics.csv',
            'company_master': 'company_master.csv',
            'peer_financials': 'data_peer_financial_metrics.csv',
            'news_snippets': 'data_peer_news_snippets.csv',
            'earnings_transcripts': 'earnings_transcripts.csv',
            'analyst_ratings': 'analyst_ratings.csv',
            'press_releases': 'snowflake_press_releases.csv',
            'sec_filings': 'snowflake_sec_filings.csv',
        }

        for key, filename in files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                self.data[key] = pd.read_csv(filepath, low_memory=False)

        # Parse dates and sort
        if 'snowflake_metrics' in self.data:
            self.data['snowflake_metrics']['PERIOD_END_DATE'] = pd.to_datetime(
                self.data['snowflake_metrics']['PERIOD_END_DATE']
            )
            self.data['snowflake_metrics'] = self.data['snowflake_metrics'].sort_values(
                'PERIOD_END_DATE', ascending=False
            )

        if 'peer_financials' in self.data:
            self.data['peer_financials']['PERIOD_END_DATE'] = pd.to_datetime(
                self.data['peer_financials']['PERIOD_END_DATE']
            )

        if 'earnings_transcripts' in self.data:
            self.data['earnings_transcripts']['EVENT_DATE'] = pd.to_datetime(
                self.data['earnings_transcripts']['EVENT_DATE']
            )
            self.data['earnings_transcripts'] = self.data['earnings_transcripts'].sort_values(
                'EVENT_DATE', ascending=False
            )

        if 'analyst_ratings' in self.data:
            self.data['analyst_ratings']['RATING_DATE'] = pd.to_datetime(
                self.data['analyst_ratings']['RATING_DATE']
            )
            self.data['analyst_ratings'] = self.data['analyst_ratings'].sort_values(
                'RATING_DATE', ascending=False
            )

        if 'news_snippets' in self.data:
            self.data['news_snippets']['NEWS_DATE'] = pd.to_datetime(
                self.data['news_snippets']['NEWS_DATE']
            )
            self.data['news_snippets'] = self.data['news_snippets'].sort_values(
                'NEWS_DATE', ascending=False
            )

        return self.data

    def get_snowflake_transcripts(self, n: int = 2) -> pd.DataFrame:
        """Get N most recent Snowflake transcripts."""
        df = self.data.get('earnings_transcripts', pd.DataFrame())
        return df[df['TICKER'] == 'SNOW'].head(n)

    def get_competitor_transcripts(self, n: int = 3) -> pd.DataFrame:
        """Get N most recent competitor transcripts."""
        df = self.data.get('earnings_transcripts', pd.DataFrame())
        return df[df['TICKER'] != 'SNOW'].head(n)

    def get_snowflake_ratings(self) -> pd.DataFrame:
        """Get Snowflake analyst ratings."""
        df = self.data.get('analyst_ratings', pd.DataFrame())
        return df[df['TICKER'] == 'SNOW']

    def get_recent_news(self, n: int = 10) -> pd.DataFrame:
        """Get recent news snippets."""
        df = self.data.get('news_snippets', pd.DataFrame())
        return df.head(n)
