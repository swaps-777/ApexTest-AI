"""Streamlit UI for Test Cases Generator AI Agent."""

import streamlit as st

from app_core import build_effective_query, get_graph
from config import DEFAULT_JIRA_ISSUE_KEY


TEST_TYPE_OPTIONS = {
    "Functional": "functional",
    "Negative": "negative",
    "Boundary": "boundary",
    "API": "api",
    "UI": "ui",
    "Regression": "regression",
}


@st.cache_resource
def init_app():
    """Seeds RAG knowledge base and builds LangGraph once."""
    return get_graph()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --surface: #ffffff;
            --surface-soft: #f7f9fc;
            --ink: #172033;
            --muted: #667085;
            --line: #d9e2ef;
            --accent: #2563eb;
            --accent-soft: #e8f0ff;
            --success-soft: #e9f9f0;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28rem),
                linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%);
            color: var(--ink);
        }

        section[data-testid="stSidebar"] {
            background: #101827;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        section[data-testid="stSidebar"] * {
            color: #eef4ff;
        }

        .block-container {
            padding-top: 2rem;
            max-width: 1220px;
        }

        .hero {
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.5rem 1.7rem;
            box-shadow: 0 18px 50px rgba(31, 45, 61, 0.08);
            margin-bottom: 1.25rem;
        }

        .hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 2rem;
            line-height: 1.15;
            letter-spacing: 0;
        }

        .hero p {
            color: var(--muted);
            margin: 0;
            font-size: 1rem;
        }

        .status-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
            min-height: 6.5rem;
            box-shadow: 0 10px 30px rgba(31, 45, 61, 0.06);
        }

        .status-card span {
            color: var(--muted);
            display: block;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.45rem;
        }

        .status-card strong {
            display: block;
            font-size: 1rem;
            line-height: 1.35;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stMultiSelect"] {
            border-radius: 8px;
        }

        .stButton button {
            border-radius: 8px;
            min-height: 2.9rem;
            font-weight: 700;
            background: var(--accent);
            border: 1px solid var(--accent);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--line);
            border-radius: 8px;
        }

        .result-shell {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 18px 50px rgba(31, 45, 61, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Test Cases Generator AI Agent",
    page_icon="TC",
    layout="wide",
)
apply_theme()

graph = init_app()

with st.sidebar:
    st.markdown("### Test Studio")
    st.caption("JIRA MCP, RAG, guardrails, and specialist QA agents.")
    st.divider()
    st.markdown("**Default story**")
    st.code(DEFAULT_JIRA_ISSUE_KEY)
    st.markdown("**Agent path**")
    st.caption("Input guardrail -> JIRA -> RAG -> specialist agents -> review.")

st.markdown(
    """
    <div class="hero">
        <h1>Test Cases Generator AI Agent</h1>
        <p>Generate traceable, deeper QA test packs from JIRA stories with RAG-grounded specialist agents.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_cols = st.columns(4)
with status_cols[0]:
    st.markdown(
        '<div class="status-card"><span>Source</span><strong>JIRA story first</strong></div>',
        unsafe_allow_html=True,
    )
with status_cols[1]:
    st.markdown(
        '<div class="status-card"><span>Context</span><strong>Testing BRD RAG</strong></div>',
        unsafe_allow_html=True,
    )
with status_cols[2]:
    st.markdown(
        '<div class="status-card"><span>Generation</span><strong>Specialist test agents</strong></div>',
        unsafe_allow_html=True,
    )
with status_cols[3]:
    st.markdown(
        '<div class="status-card"><span>Review</span><strong>Output guardrails</strong></div>',
        unsafe_allow_html=True,
    )

st.write("")
left, right = st.columns([1.25, 0.75], gap="large")

with left:
    user_query = st.text_area(
        "Request",
        value=f"Generate test cases for {DEFAULT_JIRA_ISSUE_KEY}",
        placeholder="Example: Generate test cases for SCRUM-5",
        height=112,
    )

with right:
    selected_test_type_labels = st.multiselect(
        "Specialist agents",
        options=list(TEST_TYPE_OPTIONS.keys()),
        default=list(TEST_TYPE_OPTIONS.keys()),
    )
    show_debug = st.toggle("Show debug state", value=False)
    generate = st.button("Generate Test Pack", type="primary", use_container_width=True)

if generate:
    if not user_query.strip():
        st.warning("Enter a JIRA story key or request.")
    elif not selected_test_type_labels:
        st.warning("Select at least one specialist agent.")
    else:
        selected_test_types = [TEST_TYPE_OPTIONS[label] for label in selected_test_type_labels]
        effective_query = build_effective_query(user_query, selected_test_types)

        with st.spinner("Specialist agents are generating the test pack..."):
            result = graph.invoke({"raw_user_query": user_query, "user_query": effective_query})

        st.write("")
        st.markdown('<div class="result-shell">', unsafe_allow_html=True)
        st.markdown(result.get("final_answer", "No final answer generated."))
        st.markdown("</div>", unsafe_allow_html=True)

        debug_payload = {
            "jira_key": result.get("jira_key"),
            "structured_query": result.get("structured_query"),
            "jira_score": result.get("jira_score"),
            "jira_source": result.get("jira_story", {}).get("source"),
            "rag_score": result.get("rag_score"),
            "functional_tests": len(result.get("functional_tests", [])),
            "negative_tests": len(result.get("negative_tests", [])),
            "boundary_tests": len(result.get("boundary_tests", [])),
            "api_tests": len(result.get("api_tests", [])),
            "ui_tests": len(result.get("ui_tests", [])),
            "regression_tests": len(result.get("regression_tests", [])),
            "is_safe_input": result.get("is_safe_input"),
            "is_safe_output": result.get("is_safe_output"),
        }

        if show_debug:
            with st.expander("Debug state", expanded=True):
                st.json(debug_payload)
