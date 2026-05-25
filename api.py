"""FastAPI backend for the ApexTest command center."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app_core import build_effective_query, get_graph
from config import DEFAULT_JIRA_ISSUE_KEY
from services.excel_export import build_test_pack_workbook
from services.rag_document_service import delete_document, ingest_document, list_documents
from services.response_normalizer import TEST_TYPE_STATE_KEYS, normalize_graph_result


app = FastAPI(title="ApexTest API", version="1.0.0")

cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [item.strip() for item in cors_origins.split(",") if item.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


class GenerateRequest(BaseModel):
    query: str = ""
    test_types: list[str] = Field(default_factory=list)


class ExportRequest(BaseModel):
    jira_key: str | None = None
    status: str | None = None
    summary: dict = Field(default_factory=dict)
    test_cases: list[dict] = Field(default_factory=list)
    traceability_matrix: list[dict] = Field(default_factory=list)
    coverage_summary: list[str] = Field(default_factory=list)
    final_answer: str | None = None
    debug: dict = Field(default_factory=dict)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "apextest-api",
        "default_jira_issue_key": DEFAULT_JIRA_ISSUE_KEY,
    }


@app.post("/api/generate")
def generate(request: GenerateRequest) -> dict:
    query = request.query.strip()
    test_types = [item.strip().lower() for item in request.test_types if item.strip()]

    if not query:
        raise HTTPException(status_code=400, detail="Enter a JIRA story key or natural language request.")
    if not test_types:
        raise HTTPException(status_code=400, detail="Select at least one test type.")

    unsupported = sorted(set(test_types) - set(TEST_TYPE_STATE_KEYS))
    if unsupported:
        raise HTTPException(status_code=400, detail=f"Unsupported test types: {', '.join(unsupported)}")

    try:
        effective_query = build_effective_query(query, test_types)
        result = get_graph().invoke({"raw_user_query": query, "user_query": effective_query})
        return normalize_graph_result(result)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(exc)}") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(exc)}") from None


@app.get("/api/rag/documents")
def get_rag_documents() -> dict:
    return {"documents": list_documents()}


@app.post("/api/rag/documents")
async def upload_rag_documents(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one document.")

    ingested = []
    failed = []
    for file in files:
        content = await file.read()
        try:
            ingested.append(ingest_document(file.filename or "document", content))
        except ValueError as exc:
            failed.append({"filename": file.filename, "error": str(exc)})

    if not ingested and failed:
        raise HTTPException(status_code=400, detail=failed)

    return {"documents": ingested, "failed": failed}


@app.delete("/api/rag/documents/{document_id}")
def delete_rag_document(document_id: str) -> dict:
    try:
        return delete_document(document_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Document not found.") from None


@app.post("/api/export/excel")
def export_excel(request: ExportRequest) -> Response:
    payload = request.model_dump()
    workbook = build_test_pack_workbook(payload)
    jira_key = payload.get("jira_key") or "test-pack"
    filename = f"apextest-{jira_key}.xlsx"
    return Response(
        content=workbook,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
