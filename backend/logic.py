import json
import math
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .db import db_cursor, now_iso, parse_json_field, row_to_dict

RELIABILITY = {
    "The Jackson Laboratory": 0.96,
    "Charles River": 0.94,
    "Taconic Biosciences": 0.95,
}

# -------------------------------
# Existing procurement utilities
# -------------------------------

def _load_vendors() -> List[Dict[str, Any]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM vendors")
        rows = cur.fetchall()
    vendors = []
    for r in rows:
        d = row_to_dict(r)
        d["available_strains"] = parse_json_field(d["available_strains"]) or {}
        vendors.append(d)
    return vendors


def load_vendors_snapshot() -> List[Dict[str, Any]]:
    """Expose vendors for UI/formatting layers without mutating state."""
    return _load_vendors()


def _load_strains() -> Dict[str, List[str]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM strains")
        rows = cur.fetchall()
    mapping: Dict[str, List[str]] = {}
    for r in rows:
        d = row_to_dict(r)
        mapping[d["name"]] = parse_json_field(d["equivalents"]) or []
    return mapping


def _load_cages() -> Dict[str, int]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM cages ORDER BY id LIMIT 1")
        row = cur.fetchone()
    if not row:
        return {"total_cages": 0, "mice_per_cage": 1}
    d = row_to_dict(row)
    return {"total_cages": d["total_cages"], "mice_per_cage": d["mice_per_cage"]}


def get_user_profile(conversation_id: str) -> Optional[Dict[str, Any]]:
    if not conversation_id:
        return None
    with db_cursor() as (conn, cur):
        cur.execute(
            "SELECT * FROM user_profiles WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cur.fetchone()
    return row_to_dict(row) if row else None


def upsert_user_profile(
    conversation_id: str,
    username: str,
    position: str,
    lab_institution: str,
    contact_info: str,
    email: str,
    password: str,
    shipping_address: str,
    current_mouse_count: int,
    cage_capacity: int,
) -> None:
    if not conversation_id:
        return
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            INSERT INTO user_profiles (
                conversation_id,
                username,
                position,
                lab_institution,
                contact_info,
                email,
                password,
                shipping_address,
                current_mouse_count,
                cage_capacity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                username=excluded.username,
                position=excluded.position,
                lab_institution=excluded.lab_institution,
                contact_info=excluded.contact_info,
                email=excluded.email,
                password=excluded.password,
                shipping_address=excluded.shipping_address,
                current_mouse_count=excluded.current_mouse_count,
                cage_capacity=excluded.cage_capacity
            """,
            (
                conversation_id,
                username,
                position,
                lab_institution,
                contact_info,
                email,
                password,
                shipping_address,
                current_mouse_count,
                cage_capacity,
            ),
        )


def get_cage_config() -> Dict[str, int]:
    """Expose cage configuration from the internal DB as ground-truth context."""
    return _load_cages()


# -------------------------------
# Prompt parsing + context build
# -------------------------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _extract_quantity(text: str) -> Optional[int]:
    match = re.search(r"(\d{1,4})\s*(mice|mouse|rats|rat)?", text.lower())
    if match:
        return int(match.group(1))
    return None


def _extract_age_weeks(text: str) -> Optional[int]:
    lowered = _normalize(text)
    match = re.search(r"\b(\d{1,2})\s*(week|wk)", lowered)
    if match:
        return int(match.group(1))
    return None


def _extract_experiment_start_date(text: str) -> Optional[date]:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _extract_item_hint(text: str) -> Optional[str]:
    lowered = _normalize(text)
    match = re.search(r"\b([a-z0-9]+[\-/]?[a-z0-9]+)\b", lowered)
    if match:
        return match.group(1)
    return None


def build_procurement_context(
    user_message: str,
    cage_config: Optional[Dict[str, int]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Build a context dictionary from login profile + parsed user input."""
    quantity = _extract_quantity(user_message)
    age_weeks = _extract_age_weeks(user_message)
    start_date = _extract_experiment_start_date(user_message)
    item_hint = _extract_item_hint(user_message)

    profile_current = None
    profile_capacity = None
    if user_profile:
        try:
            profile_current = int(user_profile.get("current_mouse_count", 0))
        except Exception:
            profile_current = None
        try:
            profile_capacity = int(user_profile.get("cage_capacity", 0))
        except Exception:
            profile_capacity = None

    if profile_capacity is not None:
        mice_per_cage = "not provided"
        total_cages = profile_capacity
        available_capacity = max(profile_capacity - (profile_current or 0), 0)
        required_cages = quantity if quantity is not None else None
    else:
        cage_config = cage_config or _load_cages()
        mice_per_cage = cage_config.get("mice_per_cage", 5)
        total_cages = cage_config.get("total_cages")
        required_cages = None
        if quantity:
            required_cages = int(math.ceil(quantity / float(mice_per_cage)))
        available_capacity = None

    context = {
        "requested_item": item_hint or "unknown",
        "quantity": str(quantity) if quantity else "not provided",
        "age_weeks": str(age_weeks) if age_weeks else "not provided",
        "experiment_start": start_date.isoformat() if start_date else "not provided",
        "mice_per_cage": str(mice_per_cage),
        "available_cages": str(total_cages) if total_cages is not None else "unknown",
        "required_cages": str(required_cages) if required_cages is not None else "unknown",
        "current_mouse_count": str(profile_current) if profile_current is not None else "not provided",
        "available_capacity": str(available_capacity) if available_capacity is not None else "unknown",
    }
    return context


# -------------------------------
# Legacy template fallback (only used if no LLM)
# -------------------------------

def build_chat_response(
    user_message: str,
    cage_config: Optional[Dict[str, int]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Fallback response if LLM is unavailable."""
    context = build_procurement_context(
        user_message,
        cage_config=cage_config,
        user_profile=user_profile,
    )

    capacity_line = ""
    if context.get("available_capacity") not in (None, "unknown"):
        capacity_line = (
            f"- Current mice: {context['current_mouse_count']}\n"
            f"- Total capacity: {context['available_cages']}\n"
            f"- Remaining capacity: {context['available_capacity']}\n"
        )
    else:
        capacity_line = f"- Cages available: {context['available_cages']} (estimated needed: {context['required_cages']})\n"

    reply = (
        "I can help with procurement. Based on your lab context:\n"
        f"- Requested item: {context['requested_item']}\n"
        f"- Quantity: {context['quantity']}\n"
        f"- Age: {context['age_weeks']} weeks\n"
        f"{capacity_line}\n"
        "Please provide any specific strain, vendor preference, or experiment start date."
    )
    return {"reply": reply, "email": None}


# -------------------------------
# Legacy /procure endpoint support
# -------------------------------

def procure(
    strain: str,
    quantity: int,
    experiment_start_date: date,
    approved_quota: int,
) -> Dict[str, Any]:
    """Minimal procurement result for the /procure endpoint.

    Note: The advanced chat flow now relies on LLM + RAG. This function keeps the
    legacy endpoint functional without blocking unknown strains.
    """
    vendors = _load_vendors()
    cages = _load_cages()

    # Compliance + cages checks
    compliance_ok = quantity <= approved_quota
    compliance_warning = (
        f"Requested {quantity} exceeds approved IACUC quota of {approved_quota}."
        if not compliance_ok
        else None
    )

    mice_per_cage = max(1, cages.get("mice_per_cage", 5))
    required_cages = int(math.ceil(quantity / float(mice_per_cage)))
    cages_ok = cages.get("total_cages", 0) >= required_cages
    cages_warning = (
        f"Need ~{required_cages} cages at {mice_per_cage} mice/cage, but only {cages.get('total_cages', 0)} available."
        if not cages_ok
        else None
    )

    # Choose first vendor as default allocation
    allocation = []
    selected_vendors: List[str] = []
    if vendors:
        vendor = vendors[0]
        selected_vendors.append(vendor["name"])
        allocation.append(
            {
                "vendor_id": vendor["id"],
                "vendor_name": vendor["name"],
                "quantity": quantity,
                "unit_price": vendor.get("price_per_mouse", 0.0),
                "lead_time_days": vendor.get("lead_time_days", 0),
                "shipping_cost": 0.0,
            }
        )
        lead_time_days = vendor.get("lead_time_days", 0)
    else:
        lead_time_days = 0

    latest_order_date = experiment_start_date - timedelta(days=lead_time_days)

    rfq = {
        "subject": f"Request for Quotation – {strain}",
        "body": (
            "Dear [Vendor Representative Name],\n\n"
            f"I would like to request a quotation for the following mice:\n"
            f"- Strain: {strain}\n"
            f"- Quantity: {quantity}\n"
            f"- Experiment start date: {experiment_start_date.isoformat()}\n\n"
            "Please confirm availability, lead time, and unit pricing. "
            "If this strain is unavailable, please suggest a genetically equivalent alternative.\n\n"
            "Best regards,\n[Your Name]\n[Your Institution]"
        ),
    }

    return {
        "requested_strain": strain,
        "quantity": quantity,
        "selected_vendors": selected_vendors,
        "allocation": allocation,
        "compliance": {"ok": compliance_ok, "warning": compliance_warning},
        "cages": {
            "ok": cages_ok,
            "required_cages": required_cages,
            "warning": cages_warning,
        },
        "latest_order_date": latest_order_date.isoformat(),
        "rfq": rfq,
        "strain_recommendations": [],
    }
