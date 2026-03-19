from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from .embeddings import get_embedding
from .rag_pipeline import ingest_html_text, ingest_pdf
from .rag_store import VectorStore


class RAGService:
    def __init__(self) -> None:
        root_dir = Path(__file__).resolve().parents[1]
        index_path = os.getenv("VECTOR_INDEX_PATH", str(root_dir / "db" / "vector.index"))
        meta_path = os.getenv("VECTOR_META_PATH", str(root_dir / "db" / "vector_meta.jsonl"))
        self.store = VectorStore(index_path=index_path, meta_path=meta_path)
        self.store.load()

    def ingest_pdf(self, file_path: str, source_name: str) -> int:
        docs = ingest_pdf(file_path, source_name)
        if not docs:
            return 0
        embeddings = [get_embedding(doc["text"]) for doc in docs]
        self.store.add(embeddings, docs)
        return len(docs)

    def ingest_html(self, raw_html: str, source_name: str) -> int:
        docs = ingest_html_text(raw_html, source_name)
        if not docs:
            return 0
        embeddings = [get_embedding(doc["text"]) for doc in docs]
        self.store.add(embeddings, docs)
        return len(docs)

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        embedding = get_embedding(query)
        matches = self.store.search(embedding, top_k=top_k)
        results = []
        for idx, score in matches:
            meta = self.store.get_metadata(idx)
            if not meta:
                continue
            results.append({
                "text": meta.get("text", ""),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "section": meta.get("section"),
                "score": score,
            })
        return results


rag_service = RAGService()
