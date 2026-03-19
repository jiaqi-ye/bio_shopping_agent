from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from html import escape as html_escape
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from .llm_client import can_use_openai, generate_procurement_response, generate_response
from .embeddings import get_embedding
from .logic import (
    build_chat_response,
    build_procurement_context,
    get_cage_config,
    get_user_profile,
    load_vendors_snapshot,
    upsert_user_profile,
)
from .rag_service import rag_service
from .web_scraper import default_vendor_urls, discover_vendor_urls, refresh_sources


DOMAIN_ANCHORS = [
    "I need to procure laboratory mice for an experiment and compare vendors.",
    "Requesting a quote for mouse strains with lead times and pricing.",
    "Lab procurement planning: strains, quantities, cage capacity, and compliance.",
    "Order laboratory reagents or antibodies from approved vendors.",
    "Generate an RFQ for animal procurement with shipping details.",
    "Compare vendors for research animal models and availability.",
]

IRRELEVANT_RESPONSE = (
    "This request is not related to laboratory procurement. "
    "Please ask a lab procurement question (e.g., species/strain, quantity, vendor preference, "
    "experiment start date, or budget) so I can help."
)

GREETING_RESPONSE = (
    "Hello! Tell me what you need to procure and I will draft a sourcing plan with recommended vendors, lead times, "
    "and a budget estimate."
)

KNOWN_COMPANIES = {
    "The Jackson Laboratory": "https://www.jax.org",
    "Jackson Laboratory": "https://www.jax.org",
    "JAX": "https://www.jax.org",
    "Charles River": "https://www.criver.com",
    "Taconic Biosciences": "https://www.taconic.com",
    "Taconic": "https://www.taconic.com",
    "Envigo": "https://www.envigo.com",
    "Abcam": "https://www.abcam.com",
    "Cell Signaling Technology": "https://www.cellsignal.com",
    "CST": "https://www.cellsignal.com",
    "Thermo Fisher": "https://www.thermofisher.com",
    "Invitrogen": "https://www.thermofisher.com",
    "Sigma-Aldrich": "https://www.sigmaaldrich.com",
    "Bio-Rad": "https://www.bio-rad.com",
    "Santa Cruz Biotechnology": "https://www.scbt.com",
    "R&D Systems": "https://www.rndsystems.com",
    "BioLegend": "https://www.biolegend.com",
}

COMMON_MOUSE_STRAINS = [
    "C57BL/6",
    "BALB/c",
    "Nude (nu/nu)",
    "NOD-SCID / NSG",
    "CD-1 (ICR)",
    "A/J",
    "129S (129/Sv)",
    "DBA/2",
    "FVB/N",
    "C3H",
]


COMMON_MOUSE_INFO = [
    (
        "C57BL/6 (C57 Black 6)",
        "The most widely used inbred strain and the standard genetic background for genetically modified disease models. "
        "Workhorse of virtually every field.",
    ),
    (
        "BALB/c",
        "An albino inbred strain bred for over 200 generations since 1920, widely used in immunology and cardiovascular research; "
        "noted for high anxiety and resistance to diet-induced atherosclerosis.",
    ),
    (
        "Nude mice (athymic, nu/nu)",
        "Congenitally lacking a thymus and T cells; immunodeficient. Primarily used for xenograft tumor studies.",
    ),
    (
        "NOD-SCID / NSG",
        "Severely immunodeficient (lacking T, B, and NK cells). Commonly used with patient-derived xenografts to model human disease.",
    ),
    (
        "CD-1 (ICR)",
        "An outbred stock used broadly in general-purpose studies; noted for decreased freezing in fear conditioning and potential "
        "result variability across sources.",
    ),
    (
        "A/J",
        "An inbred strain highly susceptible to lung tumors; used in cancer biology and respiratory disease research.",
    ),
    (
        "129S (129/Sv)",
        "Historically important as the strain from which embryonic stem (ES) cells were originally derived; still used in gene targeting "
        "experiments and vascular studies.",
    ),
    (
        "DBA/2",
        "One of the oldest inbred strains, originally developed by C.C. Little; the DBA strain initiated the systematic generation of "
        "inbred mouse lines.",
    ),
    (
        "FVB/N",
        "Favored for transgenic work due to large, easily injected pronuclei and large litter sizes; commonly used in oncology transgenic models.",
    ),
    (
        "C3H",
        "Inbred strain prone to spontaneous mammary tumors (due to mouse mammary tumor virus); used in cancer, immunology, and hearing research.",
    ),
]

VENDOR_PRIORITY = [
    "The Jackson Laboratory",
    "Charles River",
    "Taconic Biosciences",
]


@dataclass
class ConversationStore:
    conversations: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)

    def append(self, conversation_id: str, role: str, content: str) -> None:
        if not conversation_id:
            return
        self.conversations.setdefault(conversation_id, []).append({"role": role, "content": content})

    def history(self, conversation_id: str, limit: int = 8) -> List[Dict[str, str]]:
        if not conversation_id:
            return []
        history = self.conversations.get(conversation_id, [])
        return history[-limit:]


memory_store = ConversationStore()


_DOMAIN_EMBEDDINGS: Optional[List[List[float]]] = None


def _get_domain_embeddings() -> List[List[float]]:
    global _DOMAIN_EMBEDDINGS
    if _DOMAIN_EMBEDDINGS is None:
        _DOMAIN_EMBEDDINGS = [get_embedding(text) for text in DOMAIN_ANCHORS]
    return _DOMAIN_EMBEDDINGS


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / ((norm_a ** 0.5) * (norm_b ** 0.5))


def is_irrelevant(message: str) -> bool:
    text = (message or "").strip()
    if not text:
        return True

    # Allow simple greetings to pass through.
    if text.lower() in {"hi", "hello", "hey"}:
        return False

    query_embedding = get_embedding(text)
    anchor_embeddings = _get_domain_embeddings()
    max_similarity = max((_cosine_similarity(query_embedding, emb) for emb in anchor_embeddings), default=0.0)

    # Tuned threshold for domain relevance. Lower = more permissive, higher = stricter.
    return max_similarity < 0.22


def _clean_display_value(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    lowered = text.lower()
    blocked_values = {
        "n/a",
        "na",
        "none",
        "null",
        "unknown",
        "check vendor",
        "estimate",
        "tbd",
        "-",
    }
    if lowered in blocked_values:
        return ""

    return text


def _extract_antibody_target(message: str) -> Optional[str]:
    lowered = message.lower()
    match = None
    if "antibody" in lowered:
        match = re.search(r"\b([a-z0-9\-_/]+)\s+antibody\b", lowered, re.IGNORECASE)
    if not match:
        match = re.search(r"\banti-([a-z0-9\-_/]+)\b", lowered, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _extract_mouse_strain(message: str) -> Optional[str]:
    for strain in COMMON_MOUSE_STRAINS:
        if strain.lower() in message.lower():
            return strain
    match = re.search(r"\b([A-Za-z0-9]+(?:[/\-][A-Za-z0-9]+)+)\b", message)
    if match:
        return match.group(1)
    return None


def _extract_mouse_strains(message: str) -> List[str]:
    strains: List[str] = []
    lowered = message.lower()
    for strain in COMMON_MOUSE_STRAINS:
        if strain.lower() in lowered and strain not in strains:
            strains.append(strain)
    for match in re.findall(r"\b[A-Za-z0-9]+(?:[/\-][A-Za-z0-9]+)+\b", message):
        if match not in strains:
            strains.append(match)
    return strains


def _is_common_mice_request(message: str) -> bool:
    lowered = message.lower()
    return "common mice" in lowered or "common mouse" in lowered or "common lab mice" in lowered


def _is_vendor_exclusive_compare_request(message: str) -> bool:
    lowered = message.lower()
    return "vendor-exclusive" in lowered or "vendor exclusive" in lowered


def _parse_profile_fields(message: str) -> Dict[str, Optional[str]]:
    fields = {
        "username": None,
        "position": None,
        "lab_institution": None,
        "contact_info": None,
        "password": None,
        "shipping_address": None,
        "current_mouse_count": None,
        "cage_capacity": None,
    }
    patterns = {
        "username": r"username\s*:\s*([^\n,]+)",
        "position": r"position\s*:\s*([^\n,]+)",
        "lab_institution": r"(lab|institution)\s*:\s*([^\n,]+)",
        "contact_info": r"(contact|email|phone)\s*:\s*([^\n,]+)",
        "password": r"password\s*:\s*([^\n,]+)",
        "shipping_address": r"shipping\s*address\s*:\s*([^\n]+)",
        "current_mouse_count": r"current\s*mouse\s*count\s*:\s*(\d+)",
        "cage_capacity": r"cage\s*capacity\s*:\s*(\d+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            if key in {"lab_institution", "contact_info"} and match.lastindex and match.lastindex >= 2:
                fields[key] = match.group(2).strip()
            else:
                fields[key] = match.group(1).strip()
    return fields


def _profile_prompt(missing_fields: List[str]) -> str:
    labels = {
        "username": "Username",
        "position": "Position",
        "lab_institution": "Lab/Institution",
        "contact_info": "Contact information",
        "password": "Password",
        "shipping_address": "Shipping address",
        "current_mouse_count": "Current mouse count",
        "cage_capacity": "Cage capacity",
    }
    lines = [f"{labels[field]}:" for field in missing_fields]
    prompt = "Please provide the following:\n" + "\n".join(lines)
    return f"<div class=\"profile-prompt\"><strong>New user setup</strong><pre>{html_escape(prompt)}</pre></div>"


def _vendor_product_url(vendor_name: str, strain: Optional[str]) -> Optional[str]:
    if not strain:
        return KNOWN_COMPANIES.get(vendor_name)
    query = quote_plus(strain)
    if vendor_name in {"The Jackson Laboratory", "Jackson Laboratory", "JAX"}:
        return f"https://www.jax.org/search?query={query}"
    if vendor_name == "Charles River":
        return f"https://www.criver.com/search?searchTerm={query}"
    if vendor_name == "Taconic Biosciences":
        return f"https://www.taconic.com/search?query={query}"
    return KNOWN_COMPANIES.get(vendor_name)


def _render_vendor_link(vendor_name: str, strain: Optional[str]) -> str:
    url = _vendor_product_url(vendor_name, strain) or "#"
    return f"<a href=\"{url}\" target=\"_blank\" rel=\"noreferrer\">{html_escape(vendor_name)}</a>"


def _truncate_cell(value: str, limit: int = 22) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def _is_order_request(message: str) -> bool:
    lowered = message.lower()
    return "i want to order" in lowered or (
        "order" in lowered and any(k in lowered for k in ["mouse", "mice", "strain"])
    )


def _is_rfq_email_request(message: str) -> bool:
    lowered = message.lower()
    return any(
        phrase in lowered
        for phrase in [
            "rfq",
            "request for quotation",
            "quote",
            "quotation",
            "order email",
            "email template",
            "rfq/order email",
            "write an email",
            "write email",
            "draft email",
            "email draft",
            "email",
            "邮件",
            "写邮件",
            "邮件模板",
            "邮件草稿",
        ]
    )


def _build_order_links(strain: Optional[str]) -> str:
    vendors = load_vendors_snapshot()
    selected = []
    for name in VENDOR_PRIORITY:
        vendor = next((v for v in vendors if v.get("name") == name), None)
        if vendor:
            available = vendor.get("available_strains") or {}
            if strain and available and strain not in available:
                continue
            selected.append(name)
    if not selected:
        selected = VENDOR_PRIORITY[:3]
    links = [_render_vendor_link(name, strain) for name in selected[:3]]
    return "<br />".join(links)


def _build_rfq_email_template(
    profile: Optional[Dict[str, Any]],
    company: Optional[str],
    strain: Optional[str],
    quantity: Optional[int],
    experiment_start: Optional[str],
) -> str:
    name = (profile or {}).get("username") or "Lab Contact"
    position = (profile or {}).get("position") or ""
    lab_institution = (profile or {}).get("lab_institution") or ""
    contact_info = (profile or {}).get("contact_info") or ""
    address = (profile or {}).get("shipping_address") or "Shipping Address"
    strain_line = strain or "Strain: [please specify]"
    quantity_line = f"{quantity}" if quantity else "[quantity]"
    start_line = experiment_start or "[YYYY-MM-DD]"

    company_name = company or "Vendor"
    subject = f"RFQ: {strain_line} (Qty {quantity_line})"
    body_lines = [
        f"Hello {company_name} Team,",
        "",
        "I would like to request a quotation for the following laboratory mice:",
        f"- Strain: {strain_line}",
        f"- Quantity: {quantity_line}",
        f"- Experiment start date: {start_line}",
        f"- Shipping address: {address}",
        "",
        "Please confirm availability, lead time, unit pricing, and any shipping costs. "
        "If the requested strain is not available, please suggest a genetically equivalent alternative.",
        "",
        "Best regards,",
        name,
    ]

    if position:
        body_lines.append(position)
    if lab_institution:
        body_lines.append(lab_institution)
    if contact_info:
        body_lines.append(contact_info)

    body = "\n".join(body_lines).rstrip() + "\n"
    return (
        "<div class=\"rfq-email\">"
        f"<strong>Subject:</strong> {html_escape(subject)}<br />"
        "<pre style=\"white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;\">"
        f"{html_escape(body)}"
        "</pre></div>"
    )


def _extract_request_from_history(
    history: List[Dict[str, str]]
) -> Dict[str, Optional[str]]:
    company: Optional[str] = None
    strain: Optional[str] = None
    quantity: Optional[str] = None
    experiment_start: Optional[str] = None

    # Scan recent user messages (most recent first)
    for item in reversed(history[-8:]):
        if item.get("role") != "user":
            continue
        text = item.get("content", "")
        if not text:
            continue
        context = build_procurement_context(text, cage_config=get_cage_config())
        if not company:
            companies = _detect_companies(text)
            if companies:
                company = companies[0]
        if not strain:
            strain = _extract_mouse_strain(text)
        if not quantity and context.get("quantity") not in ("not provided", None):
            quantity = context.get("quantity")
        if not experiment_start and context.get("experiment_start") not in ("not provided", None):
            experiment_start = context.get("experiment_start")
        if strain and quantity and experiment_start:
            break

    return {
        "company": company,
        "strain": strain,
        "quantity": quantity,
        "experiment_start": experiment_start,
    }




def _detect_companies(message: str) -> List[str]:
    lowered = message.lower()
    matches: List[str] = []
    for name in KNOWN_COMPANIES.keys():
        key = name.lower()
        if len(key) <= 4:
            if re.search(rf"\b{re.escape(key)}\b", lowered):
                matches.append(name)
        elif key in lowered:
            matches.append(name)
    deduped: List[str] = []
    for name in matches:
        if name not in deduped:
            deduped.append(name)
    return deduped





def _extract_vendor_strain_meta(vendor: Dict[str, Any], strain_name: str) -> Dict[str, str]:
    available = vendor.get("available_strains") or {}
    raw = available.get(strain_name)

    result = {
        "price": "",
        "mutation_gene": "",
        "key_use": "",
    }

    vendor_price = vendor.get("price_per_mouse")
    if vendor_price not in (None, ""):
        try:
            result["price"] = f"${float(vendor_price):.2f}"
        except Exception:
            result["price"] = _clean_display_value(vendor_price)

    if isinstance(raw, dict):
        gene = _clean_display_value(raw.get("gene"))
        mutation = _clean_display_value(raw.get("mutation"))
        model = _clean_display_value(raw.get("model"))
        genotype = _clean_display_value(raw.get("genotype"))
        key_use = _clean_display_value(raw.get("use") or raw.get("key_use") or raw.get("application"))

        strain_price = raw.get("price") or raw.get("unit_price")
        if strain_price not in (None, ""):
            try:
                result["price"] = f"${float(strain_price):.2f}"
            except Exception:
                result["price"] = _clean_display_value(strain_price)

        combined = " / ".join([part for part in [gene, mutation, model, genotype] if part])
        result["mutation_gene"] = combined
        result["key_use"] = key_use
        return result

    if isinstance(raw, str):
        result["mutation_gene"] = _clean_display_value(raw)
        return result

    return result


def _render_table(headers: List[str], rows: List[List[str]], table_class: str) -> str:
    head_html = "".join([f"<th>{html_escape(h)}</th>" for h in headers])
    body_rows = []
    for row in rows:
        cells = "".join([f"<td>{cell}</td>" for cell in row])
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)
    return f"<table class=\"{table_class}\"><thead><tr>{head_html}</tr></thead><tbody>{body_html}</tbody></table>"


def _render_mouse_details(strain: Optional[str]) -> str:
    strain_label = strain or "Unspecified strain"
    headers = ["Attribute", "Details"]
    rows = [
        ["Price", "Varies by vendor and cohort size."],
        ["Gene/Mutation", "Provide the allele or mutation notation to confirm background."],
        ["Popular Company Names", "The Jackson Laboratory, Charles River, Taconic Biosciences."],
        ["Available Data/Validation", "Genotyping protocol, health status, phenotype notes, and literature references."],
        ["Other Attributes", "Background strain, breeding performance, husbandry requirements, and lead time."],
    ]
    table = _render_table(headers, rows, "detail-table")
    return f"<div class=\"detail-block\"><p><strong>Mouse Details ({html_escape(strain_label)})</strong></p>{table}</div>"


def _render_antibody_details(target: Optional[str]) -> str:
    target_label = target or "Target not specified"
    headers = ["Attribute", "Details"]
    rows = [
        ["Price", "Depends on host species, clonality, and quantity."],
        ["Gene/Mutation", "Confirm target epitope and isoform specificity."],
        ["Popular Company Names", "Abcam, Cell Signaling Technology, Thermo Fisher."],
        ["Available Data/Validation", "WB/IF/Flow validation, knockout controls, and citation history."],
        ["Other Attributes", "Host species, clonality, conjugate, recommended dilution."],
    ]
    table = _render_table(headers, rows, "detail-table")
    return f"<div class=\"detail-block\"><p><strong>Antibody Details ({html_escape(target_label)})</strong></p>{table}</div>"

def _build_reference_link(message: str, strain: Optional[str], antibody_target: Optional[str]) -> Optional[str]:
    if antibody_target or "antibody" in message.lower():
        query = quote_plus(antibody_target or "antibody")
        return f"<a href=\"https://www.abcam.com/products?keywords={query}\" target=\"_blank\" rel=\"noreferrer\">Antibody reference page</a>"
    if strain:
        query = quote_plus(strain)
        return f"<a href=\"https://www.jax.org/search?query={query}\" target=\"_blank\" rel=\"noreferrer\">Mouse strain reference page</a>"
    return None


def _render_company_links(companies: List[str]) -> str:
    if not companies:
        return ""
    links = []
    for name in companies:
        links.append(_render_vendor_link(name, None))
    if not links:
        return ""
    return "<div class=\"company-links\"><strong>References:</strong> " + " | ".join(links) + "</div>"


def _append_company_refs(message: str, reply: str) -> str:
    companies = _detect_companies(message)
    if not companies:
        return reply
    links = _render_company_links(companies)
    if not links:
        return reply
    if "<" in reply and "company-links" in reply:
        return reply
    if "<" in reply:
        return reply + links
    return _render_html_response(reply, [], companies)





def _is_mouse_query(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in ["mouse", "mice", "strain"])


def _is_antibody_query(message: str) -> bool:
    return "antibody" in message.lower()


def _render_html_response(base_text: str, extra_sections: List[str], companies: List[str]) -> str:
    escaped = html_escape(base_text).replace("\n", "<br />")
    company_links = _render_company_links(companies)
    sections = "".join(extra_sections)
    return f"<div class=\"assistant-response\"><p>{escaped}</p>{sections}{company_links}</div>"


def _render_common_mice_overview() -> str:
    items = []
    for name, description in COMMON_MOUSE_INFO:
        items.append(
            f"<li><strong>{html_escape(name)}</strong><br />{html_escape(description)}</li>"
        )
    return (
        "<div class=\"common-mice\">"
        "<p><strong>Most Common Mouse Strains (Top 10)</strong></p>"
        "<ul class=\"common-mice-list\">"
        + "".join(items)
        + "</ul>"
        "</div>"
    )


def _render_vendor_exclusive_comparison() -> str:
    headers = ["Strain", "Vendor", "Price (est.)", "Gene/Mutation", "Use"]
    rows = [
        ["C57BL/6J", "The Jackson Laboratory", "$38–$55", "Wild-type", "General-purpose baseline"],
        ["BALB/cJ", "The Jackson Laboratory", "$40–$60", "Wild-type", "Immunology, oncology"],
        ["NSG (NOD scid gamma)", "The Jackson Laboratory", "$115–$160", "Prkdc scid, Il2rg null", "Humanized / PDX"],
        ["NOD-SCID", "Charles River", "$95–$140", "Prkdc scid", "Immunodeficiency studies"],
        ["CD-1 (ICR)", "Charles River", "$25–$40", "Outbred", "General toxicology"],
        ["FVB/NJ", "The Jackson Laboratory", "$40–$65", "Wild-type", "Transgenics, pronuclear injection"],
        ["DBA/2J", "The Jackson Laboratory", "$40–$60", "Wild-type", "Aging, hearing"],
        ["129S1/SvImJ", "Taconic Biosciences", "$45–$70", "Wild-type", "Gene targeting backgrounds"],
        ["A/J", "The Jackson Laboratory", "$40–$60", "Wild-type", "Cancer susceptibility"],
        ["C3H/HeJ", "Taconic Biosciences", "$40–$65", "Tlr4 mutation", "Immunology, inflammation"],
    ]
    table = _render_table(headers, rows, "comparison-table")
    return table



def _format_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources = []
    for item in results:
        source = item.get("source")
        url = source if isinstance(source, str) and source.startswith("http") else None
        sources.append(
            {
                "source": source,
                "url": url,
                "page": item.get("page"),
                "section": item.get("section"),
                "score": item.get("score"),
            }
        )
    return sources


def _render_knowledge_fallback(results: List[Dict[str, Any]]) -> str:
    if not results:
        return (
            "I couldn't find relevant internal documents yet. "
            "Upload a PDF (protocol, SOP, or paper) and I will ground the answer in it."
        )

    excerpts = []
    for item in results:
        excerpt = item.get("text", "")
        if len(excerpt) > 380:
            excerpt = excerpt[:380].rstrip() + "..."
        label = f"{item.get('source')} (p.{item.get('page')})"
        excerpts.append(f"- {label}: {excerpt}")

    return (
        "Based on the internal documents, here are the most relevant excerpts:\n"
        + "\n".join(excerpts)
        + "\n\nLet me know if you want a specific summary or a direct citation."
    )


def handle_message(message: str, conversation_id: Optional[str], user_id: Optional[str]) -> Dict[str, Any]:
    history = memory_store.history(conversation_id or "")
    if is_irrelevant(message):
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", IRRELEVANT_RESPONSE)
        return {
            "mode": "chat",
            "message": _append_company_refs(message, IRRELEVANT_RESPONSE),
            "data": None,
            "sources": None,
        }

    profile_key = user_id or conversation_id or "default"
    profile = get_user_profile(profile_key)
    if not profile:
        fields = _parse_profile_fields(message)
        missing = [key for key, value in fields.items() if not value]
        if missing:
            prompt = _profile_prompt(missing)
            memory_store.append(conversation_id or "", "user", message)
            memory_store.append(conversation_id or "", "assistant", prompt)
            return {
                "mode": "chat",
                "message": _append_company_refs(message, prompt),
                "data": {"profile_required": True},
                "sources": None,
            }
        upsert_user_profile(
            profile_key,
            fields["username"],
            fields["position"],
            fields["lab_institution"],
            fields["contact_info"],
            fields["contact_info"],
            fields["password"],
            fields["shipping_address"],
            int(fields["current_mouse_count"]),
            int(fields["cage_capacity"]),
        )
        confirmation = "<div class=\"profile-confirm\">Profile saved.</div>"
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", confirmation)
        return {
            "mode": "chat",
            "message": _append_company_refs(message, confirmation),
            "data": {"profile_saved": True},
            "sources": None,
        }

    if message.strip().lower() in {"hi", "hello", "hey"}:
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", GREETING_RESPONSE)
        return {
            "mode": "chat",
            "message": _append_company_refs(message, GREETING_RESPONSE),
            "data": None,
            "sources": None,
        }

    if _is_common_mice_request(message):
        overview = _render_common_mice_overview()
        reply = _render_html_response(
            "Here are the 10 most commonly used mouse strains.",
            [overview],
            _detect_companies(f"{message} {overview}"),
        )
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", "Common mouse strains overview provided.")
        return {
            "mode": "procurement",
            "message": _append_company_refs(message, reply),
            "data": None,
            "sources": None,
        }

    if _is_vendor_exclusive_compare_request(message):
        paragraph = (
            "Here is a vendor-focused comparison of commonly requested mouse strains. "
            "These entries highlight typical vendor catalogs, estimated pricing ranges, and key genetic notes "
            "to help you compare options quickly. Availability and true exclusivity can change, so please verify "
            "current stock and catalog details on the vendor sites before ordering."
        )
        table = _render_vendor_exclusive_comparison()
        reply = _render_html_response(paragraph, [table], _detect_companies(message))
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", paragraph)
        return {
            "mode": "procurement",
            "message": _append_company_refs(message, reply),
            "data": None,
            "sources": None,
        }

    if _is_rfq_email_request(message):
        company = None
        companies_in_message = _detect_companies(message)
        if companies_in_message:
            company = companies_in_message[0]
        strain = _extract_mouse_strain(message)
        context = build_procurement_context(message, cage_config=get_cage_config())
        experiment_start = context.get("experiment_start") if context else None
        quantity = None
        try:
            quantity = int(context.get("quantity", "0")) if context else None
        except Exception:
            quantity = None

        history_context = _extract_request_from_history(history)
        company = company or history_context.get("company")
        strain = strain or history_context.get("strain")
        if not quantity:
            try:
                quantity = int(history_context.get("quantity") or 0)
            except Exception:
                quantity = None
        experiment_start = experiment_start or history_context.get("experiment_start")

        email_block = _build_rfq_email_template(profile, company, strain, quantity, experiment_start)
        paragraph = (
            "Below is a draft RFQ/order email template for laboratory mice. "
            "It automatically includes your profile name and shipping address, and you can edit the strain, "
            "quantity, or dates before sending."
        )
        reply = _render_html_response(paragraph, [email_block], _detect_companies(message))
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", paragraph)
        return {
            "mode": "procurement",
            "message": _append_company_refs(message, reply),
            "data": None,
            "sources": None,
        }

    if _is_order_request(message):
        strain = _extract_mouse_strain(message)
        reply = _build_order_links(strain)
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", reply)
        return {
            "mode": "procurement",
            "message": _append_company_refs(message, reply),
            "data": None,
            "sources": None,
        }

    if "protocol" in message.lower() or "pdf" in message.lower() or "paper" in message.lower():
        results = rag_service.search(message, top_k=4)
        sources = _format_sources(results)
        context = [item.get("text", "") for item in results if item.get("text")]

        reply = None
        if context and can_use_openai():
            reply = generate_response(message, context=context, history=history)

        if not reply:
            reply = _render_knowledge_fallback(results)

        memory_reply = reply
        companies = _detect_companies(f"{message} {reply}")
        if companies:
            reply = _render_html_response(reply, [], companies)

        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", memory_reply)

        return {
            "mode": "knowledge",
            "message": _append_company_refs(message, reply),
            "data": None,
            "sources": sources,
        }

    cage_config = get_cage_config()
    context = build_procurement_context(message, cage_config=cage_config)

    try:
        quantity = int(context.get("quantity", "0"))
    except Exception:
        quantity = 0
    try:
        remaining_capacity = int(profile.get("cage_capacity", 0)) - int(profile.get("current_mouse_count", 0))
    except Exception:
        remaining_capacity = 0

    if quantity and remaining_capacity >= 0 and quantity > remaining_capacity:
        limit_message = f"Order limit: {remaining_capacity}"
        memory_store.append(conversation_id or "", "user", message)
        memory_store.append(conversation_id or "", "assistant", limit_message)
        return {
            "mode": "procurement",
            "message": _append_company_refs(message, limit_message),
            "data": {"order_limit": remaining_capacity},
            "sources": None,
        }

    urls = default_vendor_urls()
    if not urls and os.getenv("ENABLE_WEB_SCRAPE", "false").lower() == "true":
        urls = discover_vendor_urls(message)

    ingested = []
    if os.getenv("ENABLE_WEB_SCRAPE", "false").lower() == "true" and urls:
        ingested = refresh_sources(urls)

    web_results = rag_service.search(message, top_k=4) if ingested else []
    web_snippets = [item.get("text", "") for item in web_results if item.get("text")]
    sources = _format_sources(web_results) if web_results else None

    reply = (
        generate_procurement_response(
            message,
            context,
            web_snippets=web_snippets,
            history=history,
        )
        if can_use_openai()
        else None
    )

    if not reply:
        response = build_chat_response(message, cage_config=cage_config)
        reply = response.get("reply", "")

    memory_reply = reply
    companies = _detect_companies(f"{message} {reply}")
    extra_sections: List[str] = []

    if extra_sections or companies:
        reply = _render_html_response(reply, extra_sections, companies)

    memory_store.append(conversation_id or "", "user", message)
    memory_store.append(conversation_id or "", "assistant", memory_reply)

    return {
        "mode": "procurement",
        "message": _append_company_refs(message, reply),
        "data": None,
        "sources": sources,
    }
