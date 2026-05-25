"""Master LangGraph workflow for Test Cases Generator AI Agent."""

from langgraph.graph import StateGraph, END

from state import TestCasesGeneratorState
from master_nodes import (
    input_guardrail_node,
    reformulator_node,
    orchestrator_node,
    requirement_quality_gate_node,
    clarification_response_node,
    aggregator_node,
    output_guardrail_node,
    tone_node,
)
from test_type_agents import (
    api_test_agent_node,
    boundary_test_agent_node,
    functional_test_agent_node,
    negative_test_agent_node,
    regression_test_agent_node,
    ui_test_agent_node,
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


def route_after_requirement_quality_gate(state: TestCasesGeneratorState) -> str:
    """Route to generation only when requirements are complete enough."""
    if state.get("requirement_quality_status") == "pass":
        return "generate"
    return "clarify"


def build_master_graph():
    """
    Builds the master graph.

    Flow:
    input_guardrail -> reformulator -> orchestrator
        -> jira_subgraph -> rag_subgraph
        -> requirement_quality_gate
        -> functional_test_agent -> negative_test_agent -> boundary_test_agent
        -> api_test_agent -> ui_test_agent -> regression_test_agent
        -> aggregator -> output_guardrail -> tone -> END
    """

    graph = StateGraph(TestCasesGeneratorState)

    # Master nodes
    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("reformulator", reformulator_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("jira_subgraph", build_jira_subgraph())
    graph.add_node("rag_subgraph", build_rag_subgraph())
    graph.add_node("requirement_quality_gate", requirement_quality_gate_node)
    graph.add_node("clarification_response", clarification_response_node)
    graph.add_node("functional_test_agent", functional_test_agent_node)
    graph.add_node("negative_test_agent", negative_test_agent_node)
    graph.add_node("boundary_test_agent", boundary_test_agent_node)
    graph.add_node("api_test_agent", api_test_agent_node)
    graph.add_node("ui_test_agent", ui_test_agent_node)
    graph.add_node("regression_test_agent", regression_test_agent_node)
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
    graph.add_edge("rag_subgraph", "requirement_quality_gate")
    graph.add_conditional_edges(
        "requirement_quality_gate",
        route_after_requirement_quality_gate,
        {
            "generate": "functional_test_agent",
            "clarify": "clarification_response",
        },
    )
    graph.add_edge("clarification_response", "output_guardrail")
    graph.add_edge("functional_test_agent", "negative_test_agent")
    graph.add_edge("negative_test_agent", "boundary_test_agent")
    graph.add_edge("boundary_test_agent", "api_test_agent")
    graph.add_edge("api_test_agent", "ui_test_agent")
    graph.add_edge("ui_test_agent", "regression_test_agent")
    graph.add_edge("regression_test_agent", "aggregator")
    graph.add_edge("aggregator", "output_guardrail")
    graph.add_edge("output_guardrail", "tone")
    graph.add_edge("tone", END)

    return graph.compile()
