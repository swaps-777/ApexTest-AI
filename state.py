"""Shared state for Test Cases Generator AI Agent LangGraph workflow."""

from typing import Any, Dict, List, TypedDict


class TestCasesGeneratorState(TypedDict, total=False):
    # Original user request
    user_query: str

    # Input guardrail result
    is_safe_input: bool
    input_rejection_reason: str

    # Reformulated query
    jira_key: str
    structured_query: Dict[str, Any]

    # Orchestrator routing flags
    use_jira: bool
    use_rag: bool
    needs_functional_tests: bool
    needs_negative_tests: bool
    needs_boundary_tests: bool
    needs_api_tests: bool
    needs_ui_tests: bool

    # JIRA subgraph outputs
    jira_story: Dict[str, Any]
    jira_story_text: str
    jira_score: float
    jira_retries: int

    # Parsed requirement
    structured_requirement: Dict[str, Any]
    feature_name: str
    acceptance_criteria: List[str]
    business_rules: List[str]
    assumptions: List[str]

    # RAG subgraph outputs
    rag_query: str
    rag_context: str
    rag_sources: List[str]
    rag_score: float
    rag_retries: int
    rag_answer: str
    rag_evaluation_reason: str

    # Test generation outputs
    functional_tests: List[Dict[str, Any]]
    negative_tests: List[Dict[str, Any]]
    boundary_tests: List[Dict[str, Any]]
    api_tests: List[Dict[str, Any]]
    ui_tests: List[Dict[str, Any]]

    # Final aggregation
    traceability_matrix: List[Dict[str, Any]]
    quality_score: float
    quality_feedback: str
    aggregated_answer: str

    # Guardrail and tone outputs
    output_safe: bool
    output_reason: str
    final_answer: str
    is_safe_output: bool
    output_rejection_reason: str

    # Export paths
    markdown_path: str
    csv_path: str

    # Error handling
    errors: List[str]