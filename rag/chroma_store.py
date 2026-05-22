"""ChromaDB store. Seeds from testing best practices and BRD docs on first run. Uses absolute paths."""

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
                    "chunk_index": i,
                }
            )

    coll.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas,
    )

    print(f"[RAG] Seeded {len(documents)} chunks from testing best practices and BRD docs")


def retrieve(query: str, k: int = RAG_TOP_K) -> list[str]:
    coll = get_collection()

    results = coll.query(
        query_texts=[query],
        n_results=k,
    )

    return results["documents"][0] if results["documents"] else []