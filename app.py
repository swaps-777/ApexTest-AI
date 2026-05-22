"""Streamlit UI for Test Cases Generator AI Agent."""

import streamlit as st

from master_graph import build_master_graph
from rag.chroma_store import seed_if_empty
from config import DEFAULT_JIRA_ISSUE_KEY


@st.cache_resource
def init_app():
    """
    Seeds RAG knowledge base and builds LangGraph once.
    """
    seed_if_empty()
    return build_master_graph()


st.set_page_config(
    page_title="Test Cases Generator AI Agent",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Test Cases Generator AI Agent")
st.caption("Generate test cases from JIRA stories using JIRA MCP + RAG + LangGraph")

graph = init_app()

with st.sidebar:
    st.header("How to use")
    st.write("Enter a JIRA story key or a natural language request.")
    st.code(f"Generate test cases for {DEFAULT_JIRA_ISSUE_KEY}")

    st.header("Architecture")
    st.write("Input Guardrail → Reformulator → Orchestrator → JIRA Subgraph → RAG Subgraph → Aggregator → Output Guardrail → Tone")

user_query = st.text_input(
    "Enter your request",
    value=f"Generate test cases for {DEFAULT_JIRA_ISSUE_KEY}",
    placeholder="Example: Generate test cases for SCRUM-5",
)

generate = st.button("Generate Test Cases", type="primary")

if generate:
    if not user_query.strip():
        st.warning("Please enter a JIRA story key or request.")
    else:
        with st.spinner("Generating test cases..."):
            result = graph.invoke({"user_query": user_query})

        st.subheader("Final Test Case Pack")
        st.markdown(result.get("final_answer", "No final answer generated."))

        with st.expander("Debug / Graph State"):
            st.json(
                {
                    "jira_key": result.get("jira_key"),
                    "structured_query": result.get("structured_query"),
                    "jira_score": result.get("jira_score"),
                    "jira_source": result.get("jira_story", {}).get("source"),
                    "rag_score": result.get("rag_score"),
                    "is_safe_input": result.get("is_safe_input"),
                    "is_safe_output": result.get("is_safe_output"),
                }
            )