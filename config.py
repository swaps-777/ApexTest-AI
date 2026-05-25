"""Single source of truth for absolute paths and config values."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# Project paths
# -------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent

SEED_DATA_DIR: Path = PROJECT_ROOT / "seed_data"
TESTING_BEST_PRACTICES_PATH: Path = SEED_DATA_DIR / "testing_best_practices.md"
BRD_SAMPLE_PATH: Path = SEED_DATA_DIR / "brd_sample.md"

CHROMA_DB_PATH: Path = PROJECT_ROOT / "chroma_db"
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
UPLOAD_DIR: Path = PROJECT_ROOT / "uploads"
RAG_UPLOAD_DIR: Path = UPLOAD_DIR / "rag_documents"
RAG_MANIFEST_PATH: Path = RAG_UPLOAD_DIR / "manifest.json"

GENERATED_MARKDOWN_PATH: Path = OUTPUT_DIR / "generated_test_cases.md"
GENERATED_CSV_PATH: Path = OUTPUT_DIR / "generated_test_cases.csv"


# -------------------------------------------------------------------
# JIRA MCP configuration
# -------------------------------------------------------------------

JIRA_MCP_COMMAND: str = "python"
JIRA_MCP_ARGS: list[str] = [str(PROJECT_ROOT / "mcp_server" / "jira_mcp_server.py")]


# -------------------------------------------------------------------
# JIRA Cloud configuration
# -------------------------------------------------------------------

JIRA_BASE_URL: str | None = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL: str | None = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN: str | None = os.getenv("JIRA_API_TOKEN")

# Default sample issue for local testing
DEFAULT_JIRA_ISSUE_KEY: str = os.getenv("DEFAULT_JIRA_ISSUE_KEY", "SCRUM-5")


# -------------------------------------------------------------------
# Chroma / RAG configuration
# -------------------------------------------------------------------

CHROMA_COLLECTION_NAME: str = "testing_best_practices"

RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))


# -------------------------------------------------------------------
# Evaluation / retry thresholds
# -------------------------------------------------------------------

SEARCH_EVAL_THRESHOLD: float = float(os.getenv("SEARCH_EVAL_THRESHOLD", "0.5"))
ANSWER_EVAL_THRESHOLD: float = float(os.getenv("ANSWER_EVAL_THRESHOLD", "0.6"))
MAX_RETRIES_PER_SUBGRAPH: int = int(os.getenv("MAX_RETRIES_PER_SUBGRAPH", "1"))


# -------------------------------------------------------------------
# LLM configuration
# -------------------------------------------------------------------

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))


# -------------------------------------------------------------------
# Test generation configuration
# -------------------------------------------------------------------

DEFAULT_TEST_TYPES: list[str] = [
    "functional",
    "negative",
    "boundary",
    "api",
    "ui",
]

DEFAULT_OUTPUT_FORMATS: list[str] = [
    "markdown",
    "csv",
]


# -------------------------------------------------------------------
# Safety / mode configuration
# -------------------------------------------------------------------

READ_ONLY_JIRA_MODE: bool = True
