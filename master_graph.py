"""Master LangGraph workflow for Test Cases Generator AI Agent."""

from langgraph.graph import StateGraph, END

from state import TestCasesGeneratorState
from master_nodes import (
    input_guardrail_node,
    reformulator_node,
    orchestrator_node,
    aggregator_node,
    output_guardrail_node,
    tone_node,
)
from subgraphs.jira_subgraph import build_jira_subgraph
from subgraphs.rag_subgraph import build_rag_subgraph


def route_after_input_guardrail(state: TestCasesGeneratorState) -> str:
    """
    If input is safe, continue to reformulator.
    Otherwise end the graph.
    """
    if state.get("is_safe_input"):
        return "reformulator"

    return "end"


def build_master_graph():
    """
    Builds the master graph.

    Flow:
    input_guardrail -> reformulator -> orchestrator
        -> jira_subgraph -> rag_subgraph
        -> aggregator -> output_guardrail -> tone -> END
    """

    graph = StateGraph(TestCasesGeneratorState)

    # Master nodes
    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("reformulator", reformulator_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("jira_subgraph", build_jira_subgraph())
    graph.add_node("rag_subgraph", build_rag_subgraph())
    graph.add_node("aggregator", aggregator_node)
    graph.add_node("output_guardrail", output_guardrail_node)
    graph.add_node("tone", tone_node)

    # Entry
    graph.set_entry_point("input_guardrail")

    # Conditional route after input guardrail
    graph.add_conditional_edges(
        "input_guardrail",
        route_after_input_guardrail,
        {
            "reformulator": "reformulator",
            "end": END,
        },
    )

    # Main flow
    graph.add_edge("reformulator", "orchestrator")
    graph.add_edge("orchestrator", "jira_subgraph")
    graph.add_edge("jira_subgraph", "rag_subgraph")
    graph.add_edge("rag_subgraph", "aggregator")
    graph.add_edge("aggregator", "output_guardrail")
    graph.add_edge("output_guardrail", "tone")
    graph.add_edge("tone", END)

    return graph.compile()