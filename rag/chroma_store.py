"""ChromaDB store for static and uploaded RAG documents."""

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION_NAME,
    TESTING_BEST_PRACTICES_PATH,
    BRD_SAMPLE_PATH,
    RAG_TOP_K,
)


def _split_markdown(text: str) -> list[str]:
    chunks, current = [], []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current:
                chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        chunks.append("\n".join(current).strip())

    return [c for c in chunks if c]


def split_text(text: str, max_chars: int = 1400, overlap: int = 180) -> list[str]:
    """Split uploaded document text into stable chunks."""
    normalized = "\n".join(line.strip() for line in text.splitlines())
    paragraphs = [part.strip() for part in normalized.split("\n\n") if part.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    if not chunks and normalized.strip():
        chunks = [normalized.strip()]

    final_chunks: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
            continue
        start = 0
        while start < len(chunk):
            final_chunks.append(chunk[start : start + max_chars].strip())
            start += max_chars - overlap

    return [chunk for chunk in final_chunks if chunk]


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    ef = DefaultEmbeddingFunction()

    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef,
    )


def seed_if_empty() -> None:
    coll = get_collection()

    if coll.count() > 0:
        return

    seed_files = [
        {
            "path": TESTING_BEST_PRACTICES_PATH,
            "source": "testing_best_practices.md",
        },
        {
            "path": BRD_SAMPLE_PATH,
            "source": "brd_sample.md",
        },
    ]

    documents = []
    ids = []
    metadatas = []

    for seed_file in seed_files:
        text = seed_file["path"].read_text(encoding="utf-8")
        chunks = _split_markdown(text)

        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            ids.append(f'{seed_file["source"]}_chunk_{i}')
            metadatas.append(
                {
                    "source": seed_file["source"],
                    "source_type": "static",
                    "document_id": seed_file["source"],
                    "filename": seed_file["source"],
                    "chunk_index": i,
                }
            )

    coll.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas,
    )

    print(f"[RAG] Seeded {len(documents)} chunks from testing best practices and BRD docs")


def add_document_chunks(document_id: str, filename: str, chunks: list[str], created_at: str) -> int:
    """Add uploaded document chunks to ChromaDB."""
    coll = get_collection()
    documents = [chunk for chunk in chunks if chunk.strip()]
    if not documents:
        return 0

    ids = [f"{document_id}_chunk_{index}" for index in range(len(documents))]
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "source": filename,
            "source_type": "uploaded",
            "chunk_index": index,
            "created_at": created_at,
        }
        for index in range(len(documents))
    ]
    coll.add(documents=documents, ids=ids, metadatas=metadatas)
    return len(documents)


def delete_document_chunks(document_id: str) -> int:
    """Delete all Chroma chunks for an uploaded document."""
    coll = get_collection()
    existing = coll.get(where={"document_id": document_id})
    ids = existing.get("ids", []) if existing else []
    if ids:
        coll.delete(ids=ids)
    return len(ids)


def retrieve_with_metadata(query: str, k: int = RAG_TOP_K) -> list[dict]:
    """Retrieve RAG chunks with metadata, preferring uploaded documents when present."""
    coll = get_collection()
    uploaded_count = _count_where(coll, {"source_type": "uploaded"})
    where = {"source_type": "uploaded"} if uploaded_count else None
    n_results = max(k, 1)

    query_kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        query_kwargs["where"] = where

    results = coll.query(**query_kwargs)
    docs = results.get("documents", [[]])[0] if results.get("documents") else []
    metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []

    return [
        {
            "text": doc,
            "metadata": metadatas[index] if index < len(metadatas) and metadatas[index] else {},
        }
        for index, doc in enumerate(docs)
    ]


def retrieve(query: str, k: int = RAG_TOP_K) -> list[str]:
    chunks = retrieve_with_metadata(query, k)
    return [chunk["text"] for chunk in chunks]


def _count_where(coll, where: dict) -> int:
    try:
        return len(coll.get(where=where).get("ids", []))
    except Exception:
        return 0
