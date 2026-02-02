# Snowflake Earnings War Room

AI-powered tool to help Snowflake's IR team anticipate analyst questions and prepare executive responses.

**Live Demo:** [https://snowearnings.streamlit.app](https://snowearnings.streamlit.app)

## Features

- **Question Generation Agent** - Autonomously researches financial data to predict tough analyst questions
- **Defense Agent** - Generates data-backed executive responses
- **Anomaly Detection** - Flags concerning trends and competitive gaps
- **3 Source Buckets** - Filings/Press, Transcripts, Analyst Research

## Data Sources

| Bucket | Description | Files |
|--------|-------------|-------|
| 1. Filings/Press | 10-Ks, 10-Qs, press releases | `snowflake_ir_metrics.csv`, `snowflake_sec_filings.csv`, `snowflake_press_releases.csv` |
| 2. Transcripts | Earnings calls (SNOW + peers) | `earnings_transcripts.csv` |
| 3. Analyst Research | Sell-side equity research | `analyst_ratings.csv` |

## Architecture

```
Streamlit UI → QuestionAgent/DefenseAgent → Tools (8 data queries) → CSV Data
```

## Run Locally

```bash
pip install -r requirements.txt
# Add ANTHROPIC_API_KEY to .streamlit/secrets.toml
streamlit run app.py
```
