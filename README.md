# ❄️ Snowflake Earnings War Room

An AI-powered prep tool for Investor Relations teams. It anticipates the tough questions Wall Street analysts are likely to ask on an earnings call, then drafts data-backed executive responses.

**Live demo:** [snowearnings.streamlit.app](https://snowearnings.streamlit.app)

> Built as my technical interview project for the Data Analytics & AI internship at Snowflake.

---

## The problem

Before every earnings call, IR teams spend days reading filings, peer transcripts, and analyst notes, trying to predict where the hard questions will come from. War Room automates the first pass: it scans the data, surfaces weak spots, and prepares talking points so the team can focus on refining answers.

## Features

- **KPI dashboard**: the latest quarter's product revenue, total revenue, RPO, net revenue retention, $1M+ customers, free cash flow, and gross margin.
- **Anomaly detection**: flags metrics that deviate sharply from recent trends and sustained NRR declines, and compares Snowflake's growth against cloud peers (AWS, Google Cloud).
- **Question Agent**: a Claude tool-use agent that researches the data (anomalies, analyst ratings, transcripts, competitor news) and generates five analyst-style questions. Each question carries a threat level, a source bucket, and the data point behind it.
- **Defense Agent**: for any question, a second agent gathers supporting evidence (positive trends, recent wins, competitive context) and drafts concise talking points plus a suggested CFO/CEO response, shown next to supporting charts.
- **Custom topics**: type a topic such as "AI product adoption" to get targeted questions on it.

## How it works

```
Launch Agent
     │
     ▼
Question Agent (Claude + tools) ──► queries CSV data through DataTools
     │                                 • check_anomalies
     │                                 • get_analyst_ratings
     │                                 • search_transcripts
     │                                 • get_competitor_news, ...
     ▼
5 analyst questions (threat level · source · data point)
     │
     ▼  "Generate Defense"
Defense Agent (Claude + tools) ──► metrics, press releases, transcripts
     │
     ▼
Talking points + suggested executive response + charts
```

## Data

| Bucket | Sources |
|--------|---------|
| 1 · Filings & press | Snowflake SEC filings (10-K/10-Q), press releases, quarterly IR metrics |
| 2 · Transcripts | Earnings call transcripts for Snowflake and peers (MDB, DDOG, TDC, AMZN, GOOGL, MSFT) |
| 3 · Analyst research | Sell-side ratings, price targets, and notes; peer financials and news |

All data lives in `data/` as CSV files.

## Tech stack

- **Python**, **Streamlit** for the UI
- **Anthropic Claude API** with tool use for the agents
- **pandas** for data processing
- **Plotly** for charts

## Project structure

```
app.py                  # Streamlit app: dashboard, agents, UI
utils/
  data_loader.py        # Loads and prepares the CSV data
  metrics_engine.py     # Anomaly detection and competitive comparison
  tools.py              # Tools the agents can call to query the data
  agent.py              # QuestionAgent, DefenseAgent, TopicQuestionGenerator
  ai_client.py          # Claude API wrapper
  charts.py             # Plotly charts
data/                   # Source CSVs
snowflake_war_room_submission.ipynb   # Project write-up
```

## Run locally

```bash
git clone https://github.com/Schadrackkarekezi/snowflake-war-room.git
cd snowflake-war-room
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then add your key: ANTHROPIC_API_KEY = "sk-..."

streamlit run app.py
```

## Author

**Schadrack Karekezi**: [GitHub](https://github.com/Schadrackkarekezi)
