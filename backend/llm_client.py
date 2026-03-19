import os
import re
from typing import Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


BASE_SYSTEM_INSTRUCTIONS = """
You are an AI Laboratory Animal Procurement Assistant.

Behavior:
- Answer naturally, and professionally.
- Use local lab context as the ground truth for lab-specific facts such as cage counts, housing limits, quotas, and internal constraints.
- Use provided web evidence when available for vendor, pricing, mutation/gene, stock, or availability details.
- If web evidence is not provided, use general knowledge or reasonable estimates.
- Do not be overly rigid, robotic, or template-like.
- Do not invent internal lab facts that are not in the provided context.
""".strip()


MOUSE_RESPONSE_INSTRUCTIONS = """
Additional formatting rules for mouse-related queries:

Scope:
- Apply these rules when the user is asking about mice, mouse strains, mouse models, stock numbers, vendors for mice, or mutation/gene details of a mouse line.
- Treat messages that only contain a strain name or shorthand (e.g., "C57BL/6J", "B6", "BALB/c", "NSG") as mouse queries.

Output format:
1. Start with one short paragraph.
2. That paragraph must include:
   - price
   - gene/mutation
   - vendor/company
3. Always add one compact HTML table (<table>...</table>) with exactly these columns:
   - Strain
   - Vendor
   - Price
   - Gene/Mutation
   - Use

Data rules:
- Do not hardcode app-side mouse data.
- Generate the content from model knowledge and/or provided web evidence.
- Prefer real data when available.
- If exact data is unavailable, use reasonable estimates instead of placeholders.
- Do not use placeholders such as N/A, TBD, unknown, unavailable, or null.

Style rules:
- Keep values short and render-friendly.
- Do not output long explanations inside table cells.
- Output the table as raw HTML (not inside markdown code fences).
- Do not show HTML tags inside the paragraph text; place the table after the paragraph.
""".strip()


def can_use_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and OpenAI is not None


def _normalize_text(text: str) -> str:
    return (text or "").strip().lower()


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _looks_like_stock_number_query(message: str) -> bool:
    lowered = _normalize_text(message)

    patterns = [
        r"^\#?\d{3,6}$",                         # 000664 / #000664
        r"^(jax|stock|strain)\s*\#?\s*\d{3,6}$",
        r"^(jax|jackson)\s+(laboratory\s+)?\#?\d{3,6}$",
        r"^(taconic|charles\s*river)\s*\#?\d{3,6}$",
    ]
    return any(re.match(pattern, lowered) for pattern in patterns)


def _contains_stock_pattern(message: str) -> bool:
    lowered = _normalize_text(message)

    patterns = [
        r"\bjax\s*\#?\s*\d{3,6}\b",
        r"\bjackson\s*(laboratory)?\s*\#?\s*\d{3,6}\b",
        r"\bstock\s*\#?\s*\d{3,6}\b",
        r"\bstrain\s*\#?\s*\d{3,6}\b",
        r"\bcat(alog)?\s*\#?\s*\d{3,8}\b",
        r"\brrid\s*[:#]?\s*[a-z0-9_\-]+\b",
    ]
    return any(re.search(pattern, lowered) for pattern in patterns)


def _contains_mouse_model_terms(message: str) -> bool:
    lowered = _normalize_text(message)

    mouse_terms = [
        "mouse", "mice", "murine", "strain", "strains", "mouse line", "mouse model",
        "vendor", "vendors", "breeder",
        "jax", "jackson", "jackson laboratory", "taconic", "charles river", "envigo",
        "c57bl/6", "c57bl/6j", "c57bl/6n", "balb/c", "balb", "cd-1", "icr",
        "b6", "b6j", "b6n", "129", "svj", "fvb", "fvbn", "dba", "a/j", "c3h",
        "nod", "scid", "nude", "rag1", "rag2", "nsg", "nsg-sgm3", "nod scid",
        "5xfad", "app/ps1", "tg2576", "apoe", "tau", "p301s", "p301l",
        "ob/ob", "db/db", "mdx", "albino", "humanized",
        "cre", "creer", "loxp", "flox", "fl/fl", "flp", "ki", "ko", "knockin",
        "knock-in", "knockout", "knock-out", "transgenic", "conditional allele",
        "老鼠", "小鼠", "鼠", "品系", "模型鼠", "转基因鼠", "敲除鼠", "敲入鼠",
        "裸鼠", "免疫缺陷鼠", "实验鼠", "突变",
    ]

    return _contains_any(lowered, mouse_terms)


def _contains_mouse_genetic_pattern(message: str) -> bool:
    lowered = _normalize_text(message)

    patterns = [
        r"\b[a-z0-9\-\._]+tm\d+[a-z0-9\-\._]*\b",
        r"\b[a-z0-9\-\._]+em\d+[a-z0-9\-\._]*\b",
        r"\btg\([^)]+\)",
        r"\bem:\d+\b",
        r"\brrid[:\s#]*[a-z0-9_\-]+\b",
        r"\b[a-z0-9]+-cre\b",
        r"\b[a-z0-9]+cre/?\+\b",
        r"\b[a-z0-9]+flox/?flox\b",
        r"\b[a-z0-9]+fl/?fl\b",
        r"\bob/ob\b",
        r"\bdb/db\b",
        r"\b5xfad\b",
        r"\bapp/ps1\b",
    ]
    return any(re.search(pattern, lowered) for pattern in patterns)


def _looks_like_strain_only(message: str) -> bool:
    raw = (message or "").strip()
    if not raw:
        return False
    lowered = raw.lower()
    if _contains_mouse_model_terms(raw) or _contains_mouse_genetic_pattern(raw) or _contains_stock_pattern(raw):
        return True
    patterns = [
        r"^(c57bl/6j|c57bl/6n|c57bl/6|balb/c|balb|cd-1|icr|129s1/svimj|129s1/sv|129/sv|fvb/n|fvbn|dba/2|a/j|c3h|nsg|nod-scid|scid|nude)$",
        r"^(b6|b6j|b6n)$",
        r"^[a-z0-9]+[/\-][a-z0-9]+$",  # generic strain-like token
        r"^[a-z0-9]+$",                 # short code like "nsg"
    ]
    return any(re.match(p, lowered) for p in patterns)


def _is_mouse_query(message: str) -> bool:
    if not message or not message.strip():
        return False

    return any([
        _contains_mouse_model_terms(message),
        _contains_stock_pattern(message),
        _looks_like_stock_number_query(message),
        _contains_mouse_genetic_pattern(message),
        _looks_like_strain_only(message),
    ])


def _build_instructions(message: str) -> str:
    instructions = [BASE_SYSTEM_INSTRUCTIONS]

    if _is_mouse_query(message):
        instructions.append(MOUSE_RESPONSE_INSTRUCTIONS)

    return "\n\n".join(instructions)


def _build_context_block(context: Optional[List[str]]) -> str:
    if not context:
        return ""

    cleaned = [item.strip() for item in context if item and item.strip()]
    if not cleaned:
        return ""

    return "\n\nContext:\n" + "\n\n".join(cleaned)


def _build_history_block(history: Optional[List[Dict[str, str]]]) -> str:
    if not history:
        return ""

    lines = []
    for item in history:
        role = str(item.get("role", "")).strip()
        content = str(item.get("content", "")).strip()
        if role and content:
            lines.append(f"{role}: {content}")

    if not lines:
        return ""

    return "\n\nRecent Conversation:\n" + "\n".join(lines)


def _build_lab_context_block(context: Optional[Dict[str, str]]) -> str:
    if not context:
        return ""

    lines = []
    for key, value in context.items():
        key_str = str(key).strip()
        value_str = str(value).strip()
        if key_str and value_str:
            lines.append(f"{key_str}: {value_str}")

    return "\n".join(lines)


def _build_web_block(web_snippets: Optional[List[str]]) -> str:
    if not web_snippets:
        return ""

    cleaned = [snippet.strip() for snippet in web_snippets if snippet and snippet.strip()]
    if not cleaned:
        return ""

    return "\n\nWeb Evidence:\n" + "\n---\n".join(cleaned)


def generate_response(
    message: str,
    context: Optional[List[str]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Optional[str]:
    if not can_use_openai():
        return None

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    context_block = _build_context_block(context)
    history_block = _build_history_block(history)

    user_input = f"User: {message}{context_block}{history_block}"

    response = client.responses.create(
        model=model,
        instructions=_build_instructions(message),
        input=user_input,
    )

    return getattr(response, "output_text", None)


def generate_procurement_response(
    message: str,
    context: Dict[str, str],
    web_snippets: Optional[List[str]] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Optional[str]:
    """
    Generate a procurement-focused response using local lab context + optional web evidence.
    """
    if not can_use_openai():
        return None

    model = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    lab_context_block = _build_lab_context_block(context)
    web_block = _build_web_block(web_snippets)
    history_block = _build_history_block(history)

    prompt = (
        "Answer the user's request using the provided information.\n\n"
        "Priority rules:\n"
        "1. Treat Local Lab Context as the source of truth for internal lab constraints.\n"
        "2. Use Web Evidence for vendor, price, mutation/gene, availability, and related market facts when provided.\n"
        "3. If exact external facts are missing, use reasonable estimates rather than placeholders.\n"
        "4. Keep the answer useful, and natural.\n\n"
        f"Local Lab Context:\n{lab_context_block if lab_context_block else '(none provided)'}"
        f"{web_block}"
        f"{history_block}\n\n"
        f"User: {message}"
    )

    response = client.responses.create(
        model=model,
        instructions=_build_instructions(message),
        input=prompt,
    )

    return getattr(response, "output_text", None)