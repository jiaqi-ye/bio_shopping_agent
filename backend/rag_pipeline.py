from __future__ import annotations

import os
import re
from typing import Dict, List

from pypdf import PdfReader


def extract_text_with_pages(file_path: str) -> List[Dict[str, str | int]]:
    reader = PdfReader(file_path)
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = " ".join(text.split())
        if text.strip():
            pages.append({"page": idx, "text": text})
    return pages


def clean_html(raw_html: str) -> str:
    # Remove script/style tags first
    cleaned = re.sub(r"<script[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
    cleaned = re.sub(r"<style[\s\S]*?</style>", " ", cleaned, flags=re.IGNORECASE)
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned


def semantic_chunk(text: str, max_chars: int = 900, overlap: int = 150) -> List[str]:
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    buffer = ""
    for sentence in sentences:
        if len(buffer) + len(sentence) + 1 <= max_chars:
            buffer = f"{buffer} {sentence}".strip()
        else:
            if buffer:
                chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)

    # Add simple overlap by appending tail of previous chunk
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                overlapped.append(chunk)
                continue
            prefix = chunks[idx - 1][-overlap:]
            overlapped.append((prefix + " " + chunk).strip())
        chunks = overlapped
    return chunks


def ingest_pdf(file_path: str, source_name: str) -> List[Dict[str, str | int]]:
    docs: List[Dict[str, str | int]] = []
    pages = extract_text_with_pages(file_path)
    for page in pages:
        for i, chunk in enumerate(semantic_chunk(page["text"])):
            docs.append({
                "text": chunk,
                "source": source_name,
                "page": int(page["page"]),
                "section": f"chunk-{i + 1}",
            })
    return docs


def ingest_html_text(raw_html: str, source_name: str) -> List[Dict[str, str | int]]:
    text = clean_html(raw_html)
    docs: List[Dict[str, str | int]] = []
    for i, chunk in enumerate(semantic_chunk(text)):
        docs.append({
            "text": chunk,
            "source": source_name,
            "page": 1,
            "section": f"chunk-{i + 1}",
        })
    return docs
