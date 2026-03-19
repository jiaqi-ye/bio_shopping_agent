import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .agent import handle_message
from .db import db_cursor, init_db, parse_json_field, row_to_dict, seed_db
from .logic import procure, get_user_profile, upsert_user_profile
from .rag_service import rag_service
from .schemas import (
    CageCreate,
    CageOut,
    CageUpdate,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    ProfileOut,
    ProcurementHistoryOut,
    ProcurementResponse,
    ProcureRequest,
    StrainCreate,
    StrainOut,
    StrainUpdate,
    VendorCreate,
    VendorOut,
    VendorUpdate,
)

load_dotenv()

app = FastAPI(title="Research Animals Procurement Agent")

origins_setting = os.getenv("CORS_ORIGINS", "*")
allow_origins = ["*"] if origins_setting == "*" else [o.strip() for o in origins_setting.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_db()


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> Dict[str, Any]:
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")
    return handle_message(payload.message, payload.conversation_id, payload.user_id)


@app.post("/api/login", response_model=ProfileOut)
def login(payload: LoginRequest) -> Dict[str, Any]:
    user_id = payload.user_id or f"user-{os.urandom(8).hex()}"
    upsert_user_profile(
        user_id,
        payload.username,
        payload.password,
        payload.shipping_address,
        payload.current_mouse_count,
        payload.cage_capacity,
    )
    profile = get_user_profile(user_id)
    return {
        "user_id": user_id,
        "username": profile.get("username"),
        "shipping_address": profile.get("shipping_address"),
        "current_mouse_count": profile.get("current_mouse_count"),
        "cage_capacity": profile.get("cage_capacity"),
    }


@app.get("/api/profile/{user_id}", response_model=ProfileOut)
def get_profile(user_id: str) -> Dict[str, Any]:
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {
        "user_id": user_id,
        "username": profile.get("username"),
        "shipping_address": profile.get("shipping_address"),
        "current_mouse_count": profile.get("current_mouse_count"),
        "cage_capacity": profile.get("cage_capacity"),
    }


@app.post("/api/upload_pdf")
def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    root_dir = Path(__file__).resolve().parents[1]
    docs_dir = root_dir / "db" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    destination = docs_dir / file.filename

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    chunk_count = rag_service.ingest_pdf(str(destination), file.filename)
    return {"filename": file.filename, "chunks": chunk_count}


@app.get("/vendors", response_model=List[VendorOut])
def list_vendors() -> List[Dict[str, Any]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM vendors ORDER BY id")
        rows = cur.fetchall()
    vendors = []
    for r in rows:
        d = row_to_dict(r)
        d["available_strains"] = parse_json_field(d["available_strains"]) or {}
        vendors.append(d)
    return vendors


@app.get("/vendors/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vendor not found")
    d = row_to_dict(row)
    d["available_strains"] = parse_json_field(d["available_strains"]) or {}
    return d


@app.post("/vendors", response_model=VendorOut)
def create_vendor(payload: VendorCreate) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        try:
            cur.execute(
                "INSERT INTO vendors (name, lead_time_days, available_strains, price_per_mouse) VALUES (?, ?, ?, ?)",
                (
                    payload.name,
                    payload.lead_time_days,
                    json.dumps(payload.available_strains),
                    payload.price_per_mouse,
                ),
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to create vendor")
        vendor_id = cur.lastrowid
    return get_vendor(vendor_id)


@app.put("/vendors/{vendor_id}", response_model=VendorOut)
def update_vendor(vendor_id: int, payload: VendorUpdate) -> Dict[str, Any]:
    existing = get_vendor(vendor_id)
    updated = existing.copy()
    for key, value in payload.dict(exclude_unset=True).items():
        updated[key] = value
    with db_cursor() as (conn, cur):
        cur.execute(
            "UPDATE vendors SET name = ?, lead_time_days = ?, available_strains = ?, price_per_mouse = ? WHERE id = ?",
            (
                updated["name"],
                updated["lead_time_days"],
                json.dumps(updated["available_strains"]),
                updated["price_per_mouse"],
                vendor_id,
            ),
        )
    return get_vendor(vendor_id)


@app.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM vendors WHERE id = ?", (vendor_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vendor not found")
    return {"deleted": True}


@app.get("/strains", response_model=List[StrainOut])
def list_strains() -> List[Dict[str, Any]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM strains ORDER BY id")
        rows = cur.fetchall()
    strains = []
    for r in rows:
        d = row_to_dict(r)
        d["equivalents"] = parse_json_field(d["equivalents"]) or []
        strains.append(d)
    return strains


@app.get("/strains/{strain_id}", response_model=StrainOut)
def get_strain(strain_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM strains WHERE id = ?", (strain_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Strain not found")
    d = row_to_dict(row)
    d["equivalents"] = parse_json_field(d["equivalents"]) or []
    return d


@app.post("/strains", response_model=StrainOut)
def create_strain(payload: StrainCreate) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        try:
            cur.execute(
                "INSERT INTO strains (name, equivalents) VALUES (?, ?)",
                (payload.name, json.dumps(payload.equivalents)),
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to create strain")
        strain_id = cur.lastrowid
    return get_strain(strain_id)


@app.put("/strains/{strain_id}", response_model=StrainOut)
def update_strain(strain_id: int, payload: StrainUpdate) -> Dict[str, Any]:
    existing = get_strain(strain_id)
    updated = existing.copy()
    for key, value in payload.dict(exclude_unset=True).items():
        updated[key] = value
    with db_cursor() as (conn, cur):
        cur.execute(
            "UPDATE strains SET name = ?, equivalents = ? WHERE id = ?",
            (
                updated["name"],
                json.dumps(updated["equivalents"]),
                strain_id,
            ),
        )
    return get_strain(strain_id)


@app.delete("/strains/{strain_id}")
def delete_strain(strain_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM strains WHERE id = ?", (strain_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Strain not found")
    return {"deleted": True}


@app.get("/cages", response_model=List[CageOut])
def list_cages() -> List[Dict[str, Any]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM cages ORDER BY id")
        rows = cur.fetchall()
    return [row_to_dict(r) for r in rows]


@app.get("/cages/{cage_id}", response_model=CageOut)
def get_cage(cage_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM cages WHERE id = ?", (cage_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Cage config not found")
    return row_to_dict(row)


@app.post("/cages", response_model=CageOut)
def create_cage(payload: CageCreate) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute(
            "INSERT INTO cages (total_cages, mice_per_cage) VALUES (?, ?)",
            (payload.total_cages, payload.mice_per_cage),
        )
        cage_id = cur.lastrowid
    return get_cage(cage_id)


@app.put("/cages/{cage_id}", response_model=CageOut)
def update_cage(cage_id: int, payload: CageUpdate) -> Dict[str, Any]:
    existing = get_cage(cage_id)
    updated = existing.copy()
    for key, value in payload.dict(exclude_unset=True).items():
        updated[key] = value
    with db_cursor() as (conn, cur):
        cur.execute(
            "UPDATE cages SET total_cages = ?, mice_per_cage = ? WHERE id = ?",
            (updated["total_cages"], updated["mice_per_cage"], cage_id),
        )
    return get_cage(cage_id)


@app.delete("/cages/{cage_id}")
def delete_cage(cage_id: int) -> Dict[str, Any]:
    with db_cursor() as (conn, cur):
        cur.execute("DELETE FROM cages WHERE id = ?", (cage_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cage config not found")
    return {"deleted": True}


@app.post("/procure", response_model=ProcurementResponse)
def procure_endpoint(payload: ProcureRequest) -> Dict[str, Any]:
    result = procure(
        payload.strain,
        payload.quantity,
        payload.experiment_start_date,
        payload.approved_quota,
    )
    if result.get("error"):
        raise HTTPException(
            status_code=400,
            detail=result["error"],
            headers={"X-Alt-Strains": ",".join(result.get("strain_recommendations", []))},
        )
    return result


@app.get("/history", response_model=List[ProcurementHistoryOut])
def history() -> List[Dict[str, Any]]:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT * FROM procurement_history ORDER BY id DESC")
        rows = cur.fetchall()
    result = []
    for r in rows:
        d = row_to_dict(r)
        d["vendors"] = parse_json_field(d["vendors"]) or []
        d["compliance_ok"] = bool(d["compliance_ok"])
        d["cages_ok"] = bool(d["cages_ok"])
        result.append(d)
    return result
