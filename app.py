"""
Snowflake Earnings War Room - Main Streamlit App
"""

import streamlit as st
from utils import DataLoader, MetricsEngine, AIClient, QuestionAgent, DefenseAgent, charts
import re

# Page config
st.set_page_config(
    page_title="Snowflake Earnings War Room",
    page_icon="❄️",
    layout="wide"
)


def init_session_state():
    """Initialize session state on first run."""
    if 'data_loaded' not in st.session_state:
        loader = DataLoader(data_dir="data")
        st.session_state.data = loader.load_all()
        st.session_state.loader = loader

        engine = MetricsEngine(
            st.session_state.data['snowflake_metrics'],
            st.session_state.data['peer_financials']
        )
        st.session_state.analysis = engine.run_analysis()
        st.session_state.kpis = engine.get_latest_kpis()

        st.session_state.data_loaded = True
        st.session_state.questions = []
        st.session_state.current_defense = None


def parse_questions(response: str) -> list:
    """Parse AI response into structured questions."""
    questions = []
    blocks = re.split(r'QUESTION:', response)[1:]

    for block in blocks:
        q = {}
        lines = block.strip().split('\n')
        q['question'] = lines[0].strip()

        for line in lines[1:]:
            if 'THREAT_LEVEL:' in line:
                q['threat'] = line.split(':')[1].strip()
            if 'SOURCE_BUCKET:' in line:
                bucket = line.split(':')[1].strip()
                bucket_names = {'1': 'Filings/Press', '2': 'Transcripts', '3': 'Analyst Research'}
                q['source'] = bucket_names.get(bucket, bucket)
            if 'DATA_POINT:' in line:
                q['data_point'] = line.split(':', 1)[1].strip()

        if q.get('question'):
            questions.append(q)

    return questions


def main():
    init_session_state()

    # Header
    st.title("❄️ Snowflake Earnings War Room")

    # Load API key
    if 'api_key' not in st.session_state:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.session_state.api_key = api_key
            st.session_state.ai_client = AIClient(api_key)
        except Exception:
            st.error("API key not configured")
            return

    # KPIs Row
    st.subheader("📊 Key Metrics")
    kpis = st.session_state.kpis
    cols = st.columns(4)
    kpi_items = [(k, v) for k, v in kpis.items() if k != 'Quarter']
    for i, (label, value) in enumerate(kpi_items[:4]):
        cols[i].metric(label, value)

    # Anomalies
    anomalies = st.session_state.analysis['anomalies']
    if anomalies:
        st.subheader("⚠️ Flagged Issues")
        for a in anomalies:
            emoji = {'HIGH': '🔴', 'MEDIUM': '🟠'}.get(a['threat'], '🟡')
            st.write(f"{emoji} **{a['metric']}**: {a['description']}")

    st.divider()

    # Question Generation
    st.subheader("🎯 Generate Analyst Questions")

    if st.button("🚀 Launch Agent", type="primary"):
        agent = QuestionAgent(
            api_key=st.session_state.api_key,
            data=st.session_state.data,
            loader=st.session_state.loader
        )

        with st.spinner("Agent researching data..."):
            for event in agent.run():
                if event['type'] in ['questions', 'complete']:
                    st.session_state.questions = parse_questions(event['content'])
                elif event['type'] == 'error':
                    st.error(event['content'])
        st.rerun()

    # Display Questions
    if st.session_state.questions:
        for i, q in enumerate(st.session_state.questions):
            threat = q.get('threat', 'MEDIUM')
            emoji = {'HIGH': '🔴', 'MEDIUM': '🟠', 'LOW': '🟡'}.get(threat, '⚪')

            col1, col2 = st.columns([6, 1])
            with col1:
                st.write(f"**{i+1}. {q['question']}**")
                st.caption(f"{emoji} {threat} | {q.get('source', 'Unknown')}")
            with col2:
                if st.button("Defend", key=f"def_{i}"):
                    st.session_state.selected_question = q
                    st.session_state.show_defense = True

    # Defense Section
    if st.session_state.get('show_defense') and st.session_state.get('selected_question'):
        st.divider()
        st.subheader("🛡️ Executive Response")
        q = st.session_state.selected_question
        st.info(q['question'])

        if st.button("Generate Response", type="primary"):
            defense_agent = DefenseAgent(
                api_key=st.session_state.api_key,
                data=st.session_state.data,
                loader=st.session_state.loader
            )

            with st.spinner("Preparing response..."):
                for event in defense_agent.run(question=q['question'], kpis=st.session_state.kpis):
                    if event['type'] in ['defense', 'complete']:
                        st.session_state.current_defense = event['content']

        if st.session_state.current_defense:
            st.markdown(st.session_state.current_defense)

            # Charts
            st.divider()
            st.subheader("📈 Supporting Data")
            tab1, tab2 = st.tabs(["Revenue", "NRR"])
            with tab1:
                st.plotly_chart(charts.revenue_trend_chart(st.session_state.data['snowflake_metrics']), use_container_width=True)
            with tab2:
                st.plotly_chart(charts.nrr_trend_chart(st.session_state.data['snowflake_metrics']), use_container_width=True)


if __name__ == "__main__":
    main()
