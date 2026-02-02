# Snowflake Earnings War Room

Helps IR teams prep for earnings calls by predicting analyst questions and drafting responses.

**Live Demo:** [snowearnings.streamlit.app](https://snowearnings.streamlit.app)

## What it does

- **Question Agent** - Looks through financial data to come up with tough questions analysts might ask
- **Defense Agent** - Finds positive metrics and drafts talking points
- **Anomaly Detection** - Flags anything that looks off (drops in FCF, declining NRR, etc.)

## Data

| Bucket | What's in it |
|--------|--------------|
| 1 | SEC filings, press releases, IR metrics |
| 2 | Earnings call transcripts (SNOW + competitors) |
| 3 | Analyst ratings and notes |

## Run locally

```bash
pip install -r requirements.txt

# Add your API key to .streamlit/secrets.toml
# ANTHROPIC_API_KEY = "sk-..."

streamlit run app.py
```
