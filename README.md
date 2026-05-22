# ApexTest AI — Test Cases Generator

A production-pattern Agentic AI system for generating test cases from JIRA stories.

This repository supports:

- React + Vite UI for the primary frontend experience
- FastAPI backend for API-driven workflows
- Custom JIRA MCP server with REST fallback
- Retrieval-Augmented Generation (RAG) using ChromaDB
- Guardrails for input, agentic execution, output, and tone
- Excel export for generated test packs
- Optional Streamlit UI for rapid local testing

## Project Structure

- `frontend/` - React + Vite frontend assets and config (primary UI)
- `api.py` - FastAPI backend entrypoint
- `app_core.py` - shared graph and query helpers for UI/API
- `config.py` - project paths and environment-based configuration
- `master_graph.py` - master graph workflow definition
- `master_nodes.py` - graph nodes used by the master workflow
- `llm.py` - LLM client and prompt handling
- `state.py` - runtime state management
- `app.py` - optional Streamlit app entrypoint for local testing
- `requirements.txt` — Python dependencies

### Key directories

- `guardrails/` — input, agentic, output, and tone guard implementations
- `mcp_clients/` — JIRA MCP client wrapper
- `mcp_server/` — local custom JIRA MCP server implementation
- `rag/` — ChromaDB store and retrieval logic
- `subgraphs/` — compiled JIRA and RAG subgraphs
- `services/` — export, document ingestion, normalization, and utilities
- `seed_data/` — RAG seed documents used for initial knowledge
- `frontend/` — Vite/React frontend assets and config
- `docs/` — architecture diagram and documentation assets
- `outputs/` — generated reports, workbooks, and exported files
- `prompts/` — prompt templates and instructions
- `chroma_db/` — local ChromaDB storage

## Getting Started

### Prerequisites

- Python 3.11+ (or a compatible Python 3.x version)
- `npm` / `pnpm` / `yarn` for frontend package management
- `git` installed
- Optional: OpenAI API key if using OpenAI-based LLM access

### Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file at the repository root and add configuration values as needed.

Example `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token
DEFAULT_JIRA_ISSUE_KEY=SCRUM-5
```

## Running the Project

### Run the React + Vite frontend (recommended)

1. Start the FastAPI backend:

```powershell
uvicorn api:app --reload --port 8000
```

2. Start the React frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the provided Vite URL in your browser to use the React app.

### Optional: Run the Streamlit UI

If you want a quick Python-only UI instead of React, run:

```powershell
streamlit run app.py
```

This starts an alternate interactive QA test case generator.

Available endpoints:

- `GET /api/health`
- `POST /api/generate`
- `GET /api/rag/documents`
- `POST /api/rag/documents`
- `DELETE /api/rag/documents/{document_id}`
- `POST /api/export/excel`

### Frontend development

From the `frontend/` directory:

```powershell
cd frontend
npm install
npm run dev
```

## RAG and Knowledge Base

The repository seeds its local ChromaDB store from:

- `seed_data/testing_best_practices.md`
- `seed_data/brd_sample.md`

The RAG logic is implemented in `rag/chroma_store.py`.

## Tests

Run the available tests with:

```powershell
pytest
```

## Notes

- `chroma_db/`, `outputs/`, `venv/`, and `frontend/node_modules/` are generated artifacts and should not be committed.
- The Streamlit app automatically seeds the RAG store on startup.
- `config.py` centralizes all path, JIRA, RAG, and LLM settings.

## Repository Summary

This project implements a hierarchical multi-agent architecture for test case generation from JIRA stories. It combines a custom JIRA MCP server, RAG-backed knowledge retrieval, guardrail enforcement, and both UI and API entry points.
