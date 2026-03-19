import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None


class VectorStore:
    def __init__(self, index_path: str, meta_path: str) -> None:
        self.index_path = Path(index_path)
        self.meta_path = Path(meta_path)
        self.metadata: List[Dict[str, Any]] = []
        self.index = None
        self.dim: Optional[int] = None

    @property
    def is_ready(self) -> bool:
        return self.index is not None and self.dim is not None

    def load(self) -> None:
        if self.meta_path.exists():
            self.metadata = [json.loads(line) for line in self.meta_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if self.index_path.exists() and faiss is not None:
            self.index = faiss.read_index(str(self.index_path))
            self.dim = self.index.d

    def _ensure_index(self, dim: int) -> None:
        if self.index is None:
            if faiss is None:
                self.index = None
                self.dim = dim
            else:
                self.index = faiss.IndexFlatIP(dim)
                self.dim = dim

    def add(self, embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        if not embeddings:
            return
        arr = np.array(embeddings, dtype="float32")
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        dim = arr.shape[1]
        self._ensure_index(dim)
        self.metadata.extend(metadatas)

        if faiss is not None and self.index is not None:
            faiss.normalize_L2(arr)
            self.index.add(arr)
            faiss.write_index(self.index, str(self.index_path))

        self._persist_metadata()

    def search(self, query_embedding: List[float], top_k: int = 4) -> List[Tuple[int, float]]:
        if not self.is_ready:
            return []
        if faiss is None or self.index is None:
            return []

        vector = np.array([query_embedding], dtype="float32")
        faiss.normalize_L2(vector)
        scores, indices = self.index.search(vector, top_k)
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))
        return results

    def _persist_metadata(self) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        with self.meta_path.open("w", encoding="utf-8") as file:
            for item in self.metadata:
                file.write(json.dumps(item, ensure_ascii=False) + "\n")

    def get_metadata(self, index: int) -> Optional[Dict[str, Any]]:
        if 0 <= index < len(self.metadata):
            return self.metadata[index]
        return None
