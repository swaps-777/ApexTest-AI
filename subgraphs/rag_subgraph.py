"""RAG subgraph for retrieving testing best practices and BRD context."""

import json

from langgraph.graph import StateGraph, END

from llm import llm
from state import TestCasesGeneratorState
from rag.chroma_store import retrieve
from guardrails.agentic_guard import check_for_rag_access


def agentic_guardrail_node(state: TestCasesGeneratorState) -> dict:
    sq = state.get("structured_query", {})
    is_safe, reason = check_for_rag_access(sq)

    if not is_safe:
        return {
            "rag_context": f"agentic guardrail blocked: {reason}",
            "rag_score": 0.0,
        }

    # Guardrail passed — return a no-op update
    return {"rag_retries": state.get("rag_retries", 0)}


def retrieval_node(state: TestCasesGeneratorState) -> dict:
    """
    Retrieves testing best practices and BRD context from ChromaDB.
    """
    sq = state.get("structured_query", {})
    jira_story_text = state.get("jira_story_text", "")

    feature = sq.get("feature", "")
    jira_key = sq.get("jira_key", "")
    intent = sq.get("intent", "generate test cases")

    query = f"""
Intent: {intent}
JIRA Key: {jira_key}
Feature: {feature}

JIRA Story:
{jira_story_text}

Retrieve relevant testing best practices, BRD business rules, validation rules,
boundary cases, negative testing guidance, API/UI testing guidance, and traceability rules.
""".strip()

    docs = retrieve(query)

    return {
        "rag_query": query,
        "rag_context": "\n\n---\n\n".join(docs),
        "rag_sources": [f"chunk_{i}" for i in range(len(docs))],
    }


def search_evaluation_node(state: TestCasesGeneratorState) -> dict:
    """
    Evaluates whether retrieved RAG context is useful for generating test cases.
    """
    rag_context = state.get("rag_context", "")
    jira_story_text = state.get("jira_story_text", "")

    prompt = f"""You are a QA RAG retrieval evaluator.

Evaluate whether the retrieved RAG context is useful for generating test cases from the JIRA story.

JIRA Story:
{jira_story_text}

Retrieved RAG Context:
{rag_context}

Score from 0.0 to 1.0.

Scoring guide:
- 1.0 = Highly relevant testing and business context
- 0.8 = Good relevant testing guidance
- 0.6 = Some useful testing guidance
- 0.3 = Weak or generic context
- 0.0 = Irrelevant or empty context

Respond with strict JSON only:
{{"score": 0.0, "reason": "..."}}
"""

    resp = llm.invoke(prompt).content.strip()
    resp = resp.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(resp)
        return {
            "rag_score": float(data.get("score", 0.0)),
            "rag_evaluation_reason": data.get("reason", ""),
        }
    except Exception:
        return {
            "rag_score": 0.5,
            "rag_evaluation_reason": "Could not parse RAG evaluation response.",
        }


def answer_evaluation_node(state: TestCasesGeneratorState) -> dict:
    """
    Creates a concise RAG answer/summary to be used by the aggregator.
    """
    rag_context = state.get("rag_context", "")
    jira_story_text = state.get("jira_story_text", "")

    prompt = f"""You are a senior QA analyst.

Using the retrieved testing best practices and BRD context, summarize what testing guidance should be applied for this JIRA story.

JIRA Story:
{jira_story_text}

Retrieved Context:
{rag_context}

Return a concise summary covering:
- Relevant business rules
- Functional testing guidance
- Negative testing guidance
- Boundary testing guidance
- API/UI/security/accessibility guidance if applicable
- Assumptions or gaps

Do not invent unsupported details.
"""

    rag_answer = llm.invoke(prompt).content.strip()

    return {
        "rag_answer": rag_answer,
    }


def build_rag_subgraph():
    """
    Builds the RAG subgraph.

    Flow:
    agentic_guardrail -> retrieval -> search_evaluation -> answer_evaluation -> END
    """
    graph = StateGraph(TestCasesGeneratorState)

    graph.add_node("agentic_guardrail", agentic_guardrail_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("search_evaluation", search_evaluation_node)
    graph.add_node("answer_evaluation", answer_evaluation_node)

    graph.set_entry_point("agentic_guardrail")
    graph.add_edge("agentic_guardrail", "retrieval")
    graph.add_edge("retrieval", "search_evaluation")
    graph.add_edge("search_evaluation", "answer_evaluation")
    graph.add_edge("answer_evaluation", END)

    return graph.compile()