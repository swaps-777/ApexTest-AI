"""Manage user-uploaded RAG documents and their ChromaDB chunks."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from docx import Document
from pypdf import PdfReader

from config import RAG_MANIFEST_PATH, RAG_UPLOAD_DIR
from rag.chroma_store import add_document_chunks, delete_document_chunks, split_text


SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def list_documents() -> list[dict]:
    """Return uploaded document metadata."""
    return _read_manifest()


def ingest_document(filename: str, content: bytes) -> dict:
    """Persist, extract, chunk, embed, and track one uploaded document."""
    original_name = Path(filename).name
    extension = Path(original_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'unknown'}")

    text = _extract_text(original_name, content)
    chunks = split_text(text)
    if not chunks:
        raise ValueError("Document did not contain extractable text.")

    RAG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    document_id = str(uuid4())
    stored_name = f"{document_id}{extension}"
    stored_path = RAG_UPLOAD_DIR / stored_name
    stored_path.write_bytes(content)

    created_at = datetime.now(timezone.utc).isoformat()
    chunk_count = add_document_chunks(document_id, original_name, chunks, created_at)

    record = {
        "document_id": document_id,
        "filename": original_name,
        "stored_path": str(stored_path),
        "chunk_count": chunk_count,
        "created_at": created_at,
        "status": "ingested",
    }
    manifest = _read_manifest()
    manifest.append(record)
    _write_manifest(manifest)
    return record


def delete_document(document_id: str) -> dict:
    """Delete uploaded document metadata, stored file, and vector chunks."""
    manifest = _read_manifest()
    record = next((item for item in manifest if item.get("document_id") == document_id), None)
    if not record:
        raise KeyError(document_id)

    deleted_chunks = delete_document_chunks(document_id)
    stored_path = Path(record.get("stored_path", ""))
    if stored_path.exists() and stored_path.is_file():
        stored_path.unlink()

    _write_manifest([item for item in manifest if item.get("document_id") != document_id])
    return {"document_id": document_id, "deleted_chunks": deleted_chunks}


def clear_documents() -> dict:
    """Delete all uploaded documents and their vector chunks."""
    deleted = 0
    for record in list(_read_manifest()):
        try:
            deleted += delete_document(record["document_id"]).get("deleted_chunks", 0)
        except KeyError:
            continue

    if RAG_UPLOAD_DIR.exists():
        for item in RAG_UPLOAD_DIR.iterdir():
            if item.name != RAG_MANIFEST_PATH.name:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink(missing_ok=True)

    _write_manifest([])
    return {"deleted_chunks": deleted}


def _extract_text(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore")
    if extension == ".docx":
        doc = Document(BytesIO(content))
        return "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported file type: {extension or 'unknown'}")


def _read_manifest() -> list[dict]:
    if not RAG_MANIFEST_PATH.exists():
        return []
    try:
        data = json.loads(RAG_MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _write_manifest(records: list[dict]) -> None:
    RAG_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RAG_MANIFEST_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
