import hashlib
import os
from typing import List, Optional

import numpy as np

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


def _fallback_embedding(text: str, dim: int = 384) -> List[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "little", signed=False)
    rng = np.random.default_rng(seed)
    vec = rng.normal(0, 1, dim).astype("float32")
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def get_embedding(text: str) -> List[float]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    if api_key and OpenAI is not None:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(model=model, input=text)
        return response.data[0].embedding

    dim = int(os.getenv("EMBEDDING_DIM", "384"))
    return _fallback_embedding(text, dim=dim)


def can_use_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and OpenAI is not None


def get_chat_model() -> Optional[str]:
    return os.getenv("CHAT_MODEL")
