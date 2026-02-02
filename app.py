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

# Custom CSS
st.markdown("""
<style>
    .threat-high { background-color: #FF4B4B; padding: 4px 8px; border-radius: 4px; }
    .threat-medium { background-color: #FFA500; padding: 4px 8px; border-radius: 4px; }
    .threat-low { background-color: #00D4AA; padding: 4px 8px; border-radius: 4px; }
    .source-tag { background-color: #29B5E8; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; }
    .kpi-card { background-color: #1E1E1E; padding: 20px; border-radius: 10px; text-align: center; }
    .kpi-value { font-size: 2em; font-weight: bold; color: #29B5E8; }
    .kpi-label { color: #888; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state on first run."""
    if 'data_loaded' not in st.session_state:
        # Load data
        loader = DataLoader(data_dir="data")
        st.session_state.data = loader.load_all()
        st.session_state.loader = loader

        # Run metrics analysis
        engine = MetricsEngine(
            st.session_state.data['snowflake_metrics'],
            st.session_state.data['peer_financials']
        )
        st.session_state.analysis = engine.run_analysis()
        st.session_state.kpis = engine.get_latest_kpis()
        st.session_state.engine = engine

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
                q['bucket'] = bucket
            if 'DATA_POINT:' in line:
                q['data_point'] = line.split(':', 1)[1].strip()

        if q.get('question'):
            questions.append(q)

    return questions


def main():
    init_session_state()

    st.title("❄️ Snowflake Earnings War Room")
    st.markdown("*Help Snowflake's IR team anticipate tough analyst questions and prepare executive responses*")

    # Load API key from secrets (backend)
    if 'api_key' not in st.session_state:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.session_state.api_key = api_key
            st.session_state.ai_client = AIClient(api_key)
        except Exception:
            st.sidebar.error("API key not configured. Add ANTHROPIC_API_KEY to secrets.")

    # Phase 1: Dashboard
    st.header("📊 Latest Quarter KPIs")
    kpis = st.session_state.kpis

    cols = st.columns(4)
    kpi_items = [(k, v) for k, v in kpis.items() if k != 'Quarter']
    for i, (label, value) in enumerate(kpi_items[:4]):
        with cols[i]:
            st.metric(label, value)

    cols2 = st.columns(4)
    for i, (label, value) in enumerate(kpi_items[4:8]):
        with cols2[i]:
            st.metric(label, value)

    st.caption(f"Data as of {kpis.get('Quarter', 'N/A')}")

    # Show detected anomalies
    st.header("⚠️ Detected Anomalies")
    anomalies = st.session_state.analysis['anomalies']

    if anomalies:
        for a in anomalies:
            threat_color = {'HIGH': '🔴', 'MEDIUM': '🟠', 'LOW': '🟡'}.get(a['threat'], '⚪')
            st.markdown(f"{threat_color} **{a['metric']}**: {a['description']}")
    else:
        st.info("No significant anomalies detected")

    # Competitive gaps
    gaps = st.session_state.analysis['competitive_gaps']
    if gaps:
        st.subheader("Competitive Position")
        for g in gaps:
            icon = "✅" if g['advantage'] else "⚠️"
            st.markdown(f"{icon} vs {g['competitor']}: Snowflake {g['snow_growth']:.1f}% vs {g['comp_growth']:.1f}% growth ({g['gap']:+.1f}pp)")

    st.divider()

    # Phase 2: Generate Questions (AGENTIC)
    st.header("🎯 Phase 2: Anticipate Analyst Questions")
    st.caption("🤖 **Agentic Mode**: AI explores data to find questions Wall Street will ask Snowflake")

    if st.button("🚀 Launch Agent", type="primary", disabled='ai_client' not in st.session_state):
        if 'ai_client' not in st.session_state:
            st.error("Please enter your Anthropic API key in the sidebar")
        else:
            # Initialize the agent
            agent = QuestionAgent(
                api_key=st.session_state.api_key,
                data=st.session_state.data,
                loader=st.session_state.loader
            )

            # Simple progress display
            status = st.empty()
            progress_bar = st.progress(0)

            status.info("🔍 Agent researching data...")
            step = 0

            for event in agent.run():
                if event['type'] == 'tool_call':
                    tool = event.get('tool', '')
                    step += 1
                    progress_bar.progress(min(step * 20, 80))
                    status.info(f"🔧 Checking: {tool.replace('_', ' ')}...")

                elif event['type'] in ['questions', 'complete']:
                    progress_bar.progress(100)
                    status.success("✅ Questions generated!")

                    # Parse and store questions
                    st.session_state.questions = parse_questions(event['content'])
                    st.session_state.raw_response = event['content']

                elif event['type'] == 'error':
                    st.error(f"Agent error: {event['content']}")

            st.rerun()

    # Display parsed questions
    if st.session_state.questions:
        st.subheader("Generated Questions")

        for i, q in enumerate(st.session_state.questions):
            threat = q.get('threat', 'MEDIUM')
            source = q.get('source', 'Unknown')
            bucket = q.get('bucket', '?')
            data_point = q.get('data_point', '')
            threat_emoji = {'HIGH': '🔴', 'MEDIUM': '🟠', 'LOW': '🟡'}.get(threat, '⚪')

            with st.container():
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{i+1}. {q['question']}**")
                    st.caption(f"{threat_emoji} {threat} | Bucket {bucket}: {source}")
                    if data_point:
                        st.caption(f"📊 *{data_point}*")
                with col2:
                    if st.button("Defend", key=f"defend_{i}"):
                        st.session_state.selected_question = q
                        st.session_state.show_defense = True
                st.divider()

        st.divider()

    # Phase 3: Defend (AGENTIC)
    if st.session_state.get('show_defense') and st.session_state.get('selected_question'):
        st.header("🛡️ Phase 3: Prepare Executive Response")
        st.caption("🤖 **Agentic Mode**: AI researches data to draft Snowflake's response")
        q = st.session_state.selected_question
        st.info(f"**Question:** {q['question']}")

        if st.button("🛡️ Generate Defense", type="primary"):
            # Initialize defense agent
            defense_agent = DefenseAgent(
                api_key=st.session_state.api_key,
                data=st.session_state.data,
                loader=st.session_state.loader
            )

            status = st.empty()
            progress_bar = st.progress(0)
            response_container = st.empty()

            status.info("🔍 Agent researching defensive data...")
            step = 0

            for event in defense_agent.run(question=q['question'], kpis=st.session_state.kpis):
                if event['type'] == 'tool_call':
                    tool = event.get('tool', '')
                    step += 1
                    progress_bar.progress(min(step * 25, 75))
                    status.info(f"🔧 Researching: {tool.replace('_', ' ')}...")

                elif event['type'] in ['defense', 'complete']:
                    progress_bar.progress(100)
                    status.success("✅ Defense generated!")
                    response_container.markdown(event['content'])
                    st.session_state.current_defense = event['content']

                elif event['type'] == 'error':
                    st.error(f"Agent error: {event['content']}")

        # Phase 4: Drill into data
        if st.session_state.current_defense:
            st.divider()
            st.header("📈 Phase 4: Drill Into Data")

            tab1, tab2, tab3, tab4 = st.tabs(["Revenue Trend", "NRR Trend", "FCF", "Customers"])

            with tab1:
                fig = charts.revenue_trend_chart(st.session_state.data['snowflake_metrics'])
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                fig = charts.nrr_trend_chart(st.session_state.data['snowflake_metrics'])
                st.plotly_chart(fig, use_container_width=True)

            with tab3:
                fig = charts.fcf_chart(st.session_state.data['snowflake_metrics'])
                st.plotly_chart(fig, use_container_width=True)

            with tab4:
                fig = charts.customer_growth_chart(st.session_state.data['snowflake_metrics'])
                st.plotly_chart(fig, use_container_width=True)

            if gaps:
                st.subheader("Competitive Comparison")
                snow_growth = gaps[0]['snow_growth'] if gaps else 0
                fig = charts.competitive_growth_chart(snow_growth, gaps)
                st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
