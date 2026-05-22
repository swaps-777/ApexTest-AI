"""Shared application services for UI and API entrypoints."""

from functools import lru_cache

from master_graph import build_master_graph
from rag.chroma_store import seed_if_empty


@lru_cache(maxsize=1)
def get_graph():
    """Seed RAG storage and build the LangGraph workflow once per process."""
    seed_if_empty()
    return build_master_graph()


def build_effective_query(user_query: str, selected_types: list[str]) -> str:
    """Add explicit test-type instructions for the reformulator."""
    cleaned_types = [test_type.strip().lower() for test_type in selected_types if test_type.strip()]
    return (
        f"{user_query.strip()}\n\n"
        f"Requested test types: {', '.join(cleaned_types)}. "
        "Generate only these selected test types using specialized agents."
    )
