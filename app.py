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

# Custom CSS to prevent green code text
st.markdown("""
<style>
code, .stMarkdown code, pre, .stMarkdown pre, p code, li code {
    color: rgba(255, 255, 255, 0.9) !important;
    background-color: transparent !important;
    font-family: inherit !important;
    font-size: inherit !important;
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)


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

    st.title("Snowflake Earnings War Room")
    st.caption("Predict analyst questions. Prepare executive responses.")

    # Load API key from secrets
    if 'api_key' not in st.session_state:
        try:
            api_key = st.secrets["ANTHROPIC_API_KEY"]
            st.session_state.api_key = api_key
            st.session_state.ai_client = AIClient(api_key)
        except Exception:
            st.sidebar.error("API key not configured. Add ANTHROPIC_API_KEY to secrets.")

    # Phase 1: Dashboard
    st.header("Latest Quarter KPIs")
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
    st.header("Detected Anomalies")
    anomalies = st.session_state.analysis['anomalies']

    if anomalies:
        for a in anomalies:
            threat_label = f"[{a['threat']}]"
            st.markdown(f"**{threat_label} {a['metric']}**: {a['description']}")
    else:
        st.info("No significant anomalies detected")

    # Competitive gaps
    gaps = st.session_state.analysis['competitive_gaps']
    if gaps:
        st.subheader("Competitive Position")
        for g in gaps:
            st.markdown(f"**Snowflake vs {g['competitor']}**: {g['snow_growth']:.1f}% vs {g['comp_growth']:.1f}% revenue growth")

    st.divider()

    # Phase 2: Generate Questions
    st.header("Phase 2: Anticipate Analyst Questions")
    st.caption("Agentic Mode: AI explores data to find questions Wall Street will ask Snowflake")

    if st.button("Launch Agent", type="primary", disabled='ai_client' not in st.session_state):
        if 'ai_client' not in st.session_state:
            st.error("Please configure API key")
        else:
            agent = QuestionAgent(
                api_key=st.session_state.api_key,
                data=st.session_state.data,
                loader=st.session_state.loader
            )

            status = st.empty()
            progress_bar = st.progress(0)

            status.info("Agent researching data...")
            step = 0

            for event in agent.run():
                if event['type'] == 'tool_call':
                    tool = event.get('tool', '')
                    step += 1
                    progress_bar.progress(min(step * 20, 80))
                    status.info(f"Checking: {tool.replace('_', ' ')}...")

                elif event['type'] in ['questions', 'complete']:
                    progress_bar.progress(100)
                    status.success("Questions generated!")
                    st.session_state.questions = parse_questions(event['content'])
                    st.session_state.raw_response = event['content']

                elif event['type'] == 'error':
                    st.error(f"Agent error: {event['content']}")

            st.rerun()

    # Custom question input
    st.divider()
    st.subheader("Or Ask About a Specific Topic")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        custom_topic = st.text_input(
            "Topic or question",
            placeholder="e.g., 'Q1 revenue slowdown' or 'AI product adoption'",
            label_visibility="collapsed"
        )
    with col_btn:
        ask_custom = st.button("Ask", type="primary", disabled='ai_client' not in st.session_state)

    # Handle custom question
    if ask_custom and custom_topic:
        if 'custom_questions' not in st.session_state:
            st.session_state.custom_questions = []

        defense_agent = DefenseAgent(
            api_key=st.session_state.api_key,
            data=st.session_state.data,
            loader=st.session_state.loader
        )

        status = st.empty()
        progress_bar = st.progress(0)

        status.info(f"Researching: {custom_topic}...")
        step = 0

        for event in defense_agent.run(question=custom_topic, kpis=st.session_state.kpis):
            if event['type'] == 'tool_call':
                tool = event.get('tool', '')
                step += 1
                progress_bar.progress(min(step * 25, 75))
                status.info(f"Researching: {tool.replace('_', ' ')}...")

            elif event['type'] in ['defense', 'complete']:
                progress_bar.progress(100)
                status.success("Response ready!")
                clean = re.sub(r'`+', '', event['content'])
                # Add to custom questions list
                st.session_state.custom_questions.append({
                    'question': custom_topic,
                    'response': clean
                })

            elif event['type'] == 'error':
                st.error(f"Error: {event['content']}")

        st.rerun()

    # Display custom questions
    if st.session_state.get('custom_questions'):
        st.subheader("Your Custom Questions")
        for idx, cq in enumerate(st.session_state.custom_questions):
            with st.expander(f"**{cq['question']}**", expanded=True):
                col_response, col_charts = st.columns([1, 1])

                with col_response:
                    st.markdown("**Executive Response:**")
                    st.markdown(cq['response'])

                with col_charts:
                    st.markdown("**Supporting Data:**")
                    chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["Revenue", "NRR", "FCF", "Customers"])
                    with chart_tab1:
                        fig = charts.revenue_trend_chart(st.session_state.data['snowflake_metrics'])
                        fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_revenue_{idx}")
                    with chart_tab2:
                        fig = charts.nrr_trend_chart(st.session_state.data['snowflake_metrics'])
                        fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_nrr_{idx}")
                    with chart_tab3:
                        fig = charts.fcf_chart(st.session_state.data['snowflake_metrics'])
                        fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_fcf_{idx}")
                    with chart_tab4:
                        fig = charts.customer_growth_chart(st.session_state.data['snowflake_metrics'])
                        fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_customers_{idx}")

    st.divider()

    # Initialize defenses storage
    if 'defenses' not in st.session_state:
        st.session_state.defenses = {}

    # Display parsed questions with inline defense
    if st.session_state.questions:
        st.subheader("Generated Questions")

        for i, q in enumerate(st.session_state.questions):
            threat = q.get('threat', 'MEDIUM')
            source = q.get('source', 'Unknown')
            bucket = q.get('bucket', '?')
            data_point = q.get('data_point', '')

            with st.expander(f"**{i+1}. {q['question']}**", expanded=True):
                st.caption(f"[{threat}] | Bucket {bucket}: {source}")
                if data_point:
                    st.caption(f"Data: {data_point}")

                # Show defense if already generated
                if i in st.session_state.defenses:
                    st.divider()

                    # Two columns: response on left, charts on right
                    col_response, col_charts = st.columns([1, 1])

                    with col_response:
                        st.markdown("**Executive Response:**")
                        # Aggressively remove all backtick patterns
                        defense_text = st.session_state.defenses[i]
                        defense_text = re.sub(r'`+', '', defense_text)
                        st.markdown(defense_text)

                    with col_charts:
                        st.markdown("**Supporting Data:**")
                        chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["Revenue", "NRR", "FCF", "Customers"])
                        with chart_tab1:
                            fig = charts.revenue_trend_chart(st.session_state.data['snowflake_metrics'])
                            fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                            st.plotly_chart(fig, use_container_width=True, key=f"revenue_{i}")
                        with chart_tab2:
                            fig = charts.nrr_trend_chart(st.session_state.data['snowflake_metrics'])
                            fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                            st.plotly_chart(fig, use_container_width=True, key=f"nrr_{i}")
                        with chart_tab3:
                            fig = charts.fcf_chart(st.session_state.data['snowflake_metrics'])
                            fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                            st.plotly_chart(fig, use_container_width=True, key=f"fcf_{i}")
                        with chart_tab4:
                            fig = charts.customer_growth_chart(st.session_state.data['snowflake_metrics'])
                            fig.update_layout(height=250, margin=dict(t=30, b=30, l=30, r=30))
                            st.plotly_chart(fig, use_container_width=True, key=f"customers_{i}")
                else:
                    # Generate defense button
                    if st.button("Generate Defense", key=f"defend_{i}", type="secondary"):
                        defense_agent = DefenseAgent(
                            api_key=st.session_state.api_key,
                            data=st.session_state.data,
                            loader=st.session_state.loader
                        )

                        status = st.empty()
                        progress_bar = st.progress(0)

                        status.info("Researching data...")
                        step = 0

                        for event in defense_agent.run(question=q['question'], kpis=st.session_state.kpis):
                            if event['type'] == 'tool_call':
                                tool = event.get('tool', '')
                                step += 1
                                progress_bar.progress(min(step * 25, 75))
                                status.info(f"Researching: {tool.replace('_', ' ')}...")

                            elif event['type'] in ['defense', 'complete']:
                                progress_bar.progress(100)
                                status.success("Defense ready!")
                                # Strip all backticks to prevent code formatting
                                clean = re.sub(r'`+', '', event['content'])
                                st.session_state.defenses[i] = clean
                                st.session_state.current_defense = clean

                            elif event['type'] == 'error':
                                st.error(f"Error: {event['content']}")

                        st.rerun()


if __name__ == "__main__":
    main()
