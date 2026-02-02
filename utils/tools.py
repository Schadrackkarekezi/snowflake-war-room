"""Tools for querying the CSV data."""

import pandas as pd


class DataTools:
    """Tools the AI agent can call to look at the data."""

    def __init__(self, data: dict, loader):
        self.data = data
        self.loader = loader

    def get_tool_definitions(self) -> list:
        """Return tool definitions for Claude API."""
        return [
            {
                "name": "get_snowflake_metrics",
                "description": "Get Snowflake's financial metrics (revenue, NRR, RPO, FCF, margins, customer counts) for specified quarters. Use this to find trends, anomalies, or specific data points.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric to retrieve: 'all', 'revenue', 'nrr', 'rpo', 'fcf', 'margins', 'customers'",
                            "enum": ["all", "revenue", "nrr", "rpo", "fcf", "margins", "customers"]
                        },
                        "quarters": {
                            "type": "integer",
                            "description": "Number of recent quarters to return (default 4)",
                            "default": 4
                        }
                    },
                    "required": ["metric"]
                }
            },
            {
                "name": "search_transcripts",
                "description": "Search earnings call transcripts for specific topics or keywords. Returns relevant excerpts from Snowflake and/or competitor calls.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword or topic to search for (e.g., 'AI', 'consumption', 'pricing', 'competition')"
                        },
                        "company": {
                            "type": "string",
                            "description": "Filter by company: 'SNOW', 'all', or competitor ticker like 'DDOG', 'MDB'",
                            "default": "all"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results to return",
                            "default": 3
                        }
                    },
                    "required": ["keyword"]
                }
            },
            {
                "name": "get_analyst_ratings",
                "description": "Get analyst ratings, price targets, and research notes for Snowflake or competitors.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company": {
                            "type": "string",
                            "description": "Company ticker: 'SNOW' or competitor ticker",
                            "default": "SNOW"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_competitor_news",
                "description": "Get recent news and headlines about competitors. Useful for finding competitive threats or market trends.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Competitor ticker (e.g., 'DDOG', 'MDB', 'ORCL') or 'all' for all competitors",
                            "default": "all"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "check_anomalies",
                "description": "Detect anomalies and concerning trends in Snowflake's metrics. Returns flagged issues with threat levels.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_sec_filings",
                "description": "Get recent SEC filings (10-K, 10-Q) for Snowflake with filing dates and summaries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filing_type": {
                            "type": "string",
                            "description": "Type of filing: 'all', '10-K', '10-Q'",
                            "default": "all"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max filings to return",
                            "default": 3
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_press_releases",
                "description": "Get recent Snowflake press releases with titles, dates, and summaries.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Optional keyword to filter press releases",
                            "default": ""
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max releases to return",
                            "default": 5
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "compare_to_competitor",
                "description": "Compare Snowflake's metrics directly to a specific competitor's metrics.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "competitor": {
                            "type": "string",
                            "description": "Competitor ticker to compare against (e.g., 'DDOG', 'MDB', 'ORCL')"
                        },
                        "metric": {
                            "type": "string",
                            "description": "Metric to compare: 'revenue_growth', 'all'",
                            "default": "all"
                        }
                    },
                    "required": ["competitor"]
                }
            },
            {
                "name": "generate_questions",
                "description": "Call this ONLY when you have gathered enough information. Generates the final analyst questions based on your research.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "findings": {
                            "type": "string",
                            "description": "Summary of your key findings that should inform the questions"
                        }
                    },
                    "required": ["findings"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result as a string."""

        if tool_name == "get_snowflake_metrics":
            return self._get_snowflake_metrics(
                tool_input.get("metric", "all"),
                tool_input.get("quarters", 4)
            )

        elif tool_name == "search_transcripts":
            return self._search_transcripts(
                tool_input.get("keyword", ""),
                tool_input.get("company", "all"),
                tool_input.get("limit", 3)
            )

        elif tool_name == "get_analyst_ratings":
            return self._get_analyst_ratings(
                tool_input.get("company", "SNOW")
            )

        elif tool_name == "get_competitor_news":
            return self._get_competitor_news(
                tool_input.get("ticker", "all")
            )

        elif tool_name == "check_anomalies":
            return self._check_anomalies()

        elif tool_name == "get_sec_filings":
            return self._get_sec_filings(
                tool_input.get("filing_type", "all"),
                tool_input.get("limit", 3)
            )

        elif tool_name == "get_press_releases":
            return self._get_press_releases(
                tool_input.get("keyword", ""),
                tool_input.get("limit", 5)
            )

        elif tool_name == "compare_to_competitor":
            return self._compare_to_competitor(
                tool_input.get("competitor", ""),
                tool_input.get("metric", "all")
            )

        elif tool_name == "generate_questions":
            return "GENERATE_QUESTIONS:" + tool_input.get("findings", "")

        else:
            return f"Unknown tool: {tool_name}"

    def _get_snowflake_metrics(self, metric: str, quarters: int) -> str:
        """Get Snowflake metrics."""
        df = self.data['snowflake_metrics'].tail(quarters)

        if metric == "all":
            result = df.to_string()
        elif metric == "revenue":
            cols = ['FISCAL_QUARTER', 'PRODUCT_REVENUE_M', 'TOTAL_REVENUE_M']
            result = df[[c for c in cols if c in df.columns]].to_string()
        elif metric == "nrr":
            cols = ['FISCAL_QUARTER', 'NRR_PERCENT']
            result = df[[c for c in cols if c in df.columns]].to_string()
        elif metric == "rpo":
            cols = ['FISCAL_QUARTER', 'RPO_M']
            result = df[[c for c in cols if c in df.columns]].to_string()
        elif metric == "fcf":
            cols = ['FISCAL_QUARTER', 'FCF_IN_MILLIONS']
            result = df[[c for c in cols if c in df.columns]].to_string()
        elif metric == "margins":
            cols = ['FISCAL_QUARTER', 'GROSS_MARGIN_PERCENT']
            result = df[[c for c in cols if c in df.columns]].to_string()
        elif metric == "customers":
            cols = ['FISCAL_QUARTER', 'CUSTOMERS_1M_PLUS']
            result = df[[c for c in cols if c in df.columns]].to_string()
        else:
            result = df.to_string()

        return f"SNOWFLAKE METRICS ({quarters} quarters):\n{result}"

    def _search_transcripts(self, keyword: str, company: str, limit: int) -> str:
        """Search earnings transcripts."""
        df = self.data['earnings_transcripts']

        if company != "all":
            df = df[df['TICKER'] == company.upper()]

        if keyword:
            mask = df['SYNOPSIS'].str.contains(keyword, case=False, na=False)
            df = df[mask]

        df = df.head(limit)

        if df.empty:
            return f"No transcripts found for keyword '{keyword}' and company '{company}'"

        results = []
        for _, row in df.iterrows():
            synopsis = row.get('SYNOPSIS', '')[:500] if row.get('SYNOPSIS') else 'No synopsis'
            results.append(f"[{row.get('TICKER', '')}] {row.get('EVENT_TYPE', '')} ({row.get('EVENT_DATE', '')}):\n{synopsis}\n")

        return "TRANSCRIPT SEARCH RESULTS:\n" + "\n---\n".join(results)

    def _get_analyst_ratings(self, company: str) -> str:
        """Get analyst ratings."""
        df = self.data['analyst_ratings']

        if company != "all":
            df = df[df['TICKER'] == company.upper()]

        if df.empty:
            return f"No analyst ratings found for {company}"

        results = []
        for _, row in df.iterrows():
            results.append(
                f"- {row.get('ANALYST_FIRM', 'Unknown')}: {row.get('RATING', '')} "
                f"(PT ${row.get('PRICE_TARGET', 'N/A')}) - \"{row.get('NOTES', '')}\""
            )

        return f"ANALYST RATINGS FOR {company}:\n" + "\n".join(results)

    def _get_competitor_news(self, ticker: str) -> str:
        """Get competitor news."""
        df = self.data['news_snippets']

        if ticker != "all":
            df = df[df['TICKER'] == ticker.upper()]

        if df.empty:
            return f"No news found for {ticker}"

        results = []
        for _, row in df.iterrows():
            summary = row.get('SUMMARY', '')[:200] if row.get('SUMMARY') else ''
            results.append(f"[{row.get('TICKER', '')}] {row.get('HEADLINE', '')}: {summary}")

        return "COMPETITOR NEWS:\n" + "\n\n".join(results)

    def _check_anomalies(self) -> str:
        """Check for anomalies using MetricsEngine."""
        from utils.metrics_engine import MetricsEngine

        engine = MetricsEngine(
            self.data['snowflake_metrics'],
            self.data['peer_financials']
        )
        analysis = engine.run_analysis()

        anomalies = analysis.get('anomalies', [])
        gaps = analysis.get('competitive_gaps', [])

        result = "DETECTED ANOMALIES:\n"
        if anomalies:
            for a in anomalies:
                result += f"- [{a['threat']}] {a['metric']}: {a['description']}\n"
        else:
            result += "- No major anomalies detected\n"

        result += "\nCOMPETITIVE GAPS:\n"
        if gaps:
            for g in gaps:
                status = "ahead" if g['advantage'] else "behind"
                result += f"- vs {g['competitor']}: SNOW {g['snow_growth']:.1f}% vs {g['comp_growth']:.1f}% ({status})\n"

        return result

    def _get_sec_filings(self, filing_type: str, limit: int) -> str:
        """Get SEC filings."""
        df = self.data['sec_filings']

        if filing_type != "all":
            df = df[df['FILING_TYPE'] == filing_type]

        df = df.head(limit)

        if df.empty:
            return f"No SEC filings found for type '{filing_type}'"

        results = []
        for _, row in df.iterrows():
            results.append(f"- {row.get('FILING_TYPE', '')} filed {row.get('FILING_DATE', '')}")

        return "SEC FILINGS:\n" + "\n".join(results)

    def _get_press_releases(self, keyword: str, limit: int) -> str:
        """Get press releases."""
        df = self.data['press_releases']

        if keyword:
            mask = df['TITLE'].str.contains(keyword, case=False, na=False)
            df = df[mask]

        df = df.head(limit)

        if df.empty:
            return f"No press releases found" + (f" for keyword '{keyword}'" if keyword else "")

        results = []
        for _, row in df.iterrows():
            synopsis = row.get('SYNOPSIS', '')[:200] if row.get('SYNOPSIS') else ''
            results.append(f"[{row.get('RELEASE_DATE', '')}] {row.get('TITLE', '')}: {synopsis}")

        return "PRESS RELEASES:\n" + "\n\n".join(results)

    def _compare_to_competitor(self, competitor: str, metric: str) -> str:
        """Compare Snowflake to a competitor."""
        peer_df = self.data['peer_financials']
        snow_df = self.data['snowflake_metrics']

        # peer_financials uses COMPANY_ID column
        comp_data = peer_df[peer_df['COMPANY_ID'] == competitor.upper()]

        if comp_data.empty:
            return f"No data found for competitor '{competitor}'. Available companies: {peer_df['COMPANY_ID'].unique().tolist()}"

        result = f"COMPARISON: SNOWFLAKE vs {competitor.upper()}\n\n"

        # Get latest Snowflake metrics
        snow_latest = snow_df.iloc[-1] if not snow_df.empty else {}
        result += "SNOWFLAKE (latest):\n"
        result += f"- Revenue: ${snow_latest.get('TOTAL_REVENUE_M', 'N/A')}M\n"
        result += f"- NRR: {snow_latest.get('NRR_PERCENT', 'N/A')}%\n"

        # Get competitor metrics (pivot the data since it's in long format)
        result += f"\n{competitor.upper()} metrics:\n"
        for _, row in comp_data.iterrows():
            metric_name = row.get('METRIC_NAME', '')
            metric_value = row.get('METRIC_VALUE', '')
            metric_unit = row.get('METRIC_UNIT', '')
            quarter = row.get('FISCAL_QUARTER', '')
            year = row.get('FISCAL_YEAR', '')
            result += f"- {metric_name}: {metric_value} {metric_unit} (FY{year} Q{quarter})\n"

        return result
