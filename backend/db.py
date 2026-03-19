import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("DATABASE_PATH", str(ROOT_DIR / "db" / "procurement.db"))


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        yield conn, conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_cursor() as (conn, cur):
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                lead_time_days INTEGER NOT NULL,
                available_strains TEXT NOT NULL,
                price_per_mouse REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS strains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                equivalents TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_cages INTEGER NOT NULL,
                mice_per_cage INTEGER NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS procurement_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strain TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                vendors TEXT NOT NULL,
                date TEXT NOT NULL,
                compliance_ok INTEGER NOT NULL,
                cages_ok INTEGER NOT NULL
            )
            """
        )
        # Added: user profile storage for inventory-aware ordering
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                conversation_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                position TEXT NOT NULL,
                lab_institution TEXT NOT NULL,
                contact_info TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                current_mouse_count INTEGER NOT NULL,
                cage_capacity INTEGER NOT NULL
            )
            """
        )

        # Ensure new columns exist for existing databases.
        cur.execute("PRAGMA table_info(user_profiles)")
        existing_cols = {row[1] for row in cur.fetchall()}
        required_cols = {
            "position": "TEXT NOT NULL DEFAULT ''",
            "lab_institution": "TEXT NOT NULL DEFAULT ''",
            "contact_info": "TEXT NOT NULL DEFAULT ''",
            "email": "TEXT NOT NULL DEFAULT ''",
        }
        for col, col_def in required_cols.items():
            if col not in existing_cols:
                cur.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} {col_def}")


def seed_db() -> None:
    with db_cursor() as (conn, cur):
        cur.execute("SELECT COUNT(*) AS c FROM vendors")
        if cur.fetchone()["c"] == 0:
            vendors = [
                {
                    "name": "The Jackson Laboratory",
                    "lead_time_days": 14,
                    "available_strains": {
                        "C57BL/6J": 30,
                        "BALB/c": 40,
                        "DBA/2": 20,
                        "FVB/N": 15,
                    },
                    "price_per_mouse": 38.0,
                },
                {
                    "name": "Charles River",
                    "lead_time_days": 10,
                    "available_strains": {
                        "C57BL/6J": 25,
                        "BALB/c": 35,
                        "129S1/SvImJ": 15,
                    },
                    "price_per_mouse": 36.5,
                },
                {
                    "name": "Taconic Biosciences",
                    "lead_time_days": 12,
                    "available_strains": {
                        "C57BL/6J": 20,
                        "DBA/2": 25,
                        "FVB/N": 30,
                        "129S1/SvImJ": 10,
                    },
                    "price_per_mouse": 37.0,
                },
            ]
            for v in vendors:
                cur.execute(
                    "INSERT INTO vendors (name, lead_time_days, available_strains, price_per_mouse) VALUES (?, ?, ?, ?)",
                    (
                        v["name"],
                        v["lead_time_days"],
                        json.dumps(v["available_strains"]),
                        v["price_per_mouse"],
                    ),
                )

        cur.execute("SELECT COUNT(*) AS c FROM strains")
        if cur.fetchone()["c"] == 0:
            strains = [
                {
                    "name": "C57BL/6J",
                    "equivalents": ["C57BL/6N", "C57BL/6Tac"],
                },
                {"name": "BALB/c", "equivalents": ["BALB/cJ"]},
                {"name": "DBA/2", "equivalents": ["DBA/2J"]},
                {"name": "FVB/N", "equivalents": ["FVB/NJ"]},
                {
                    "name": "129S1/SvImJ",
                    "equivalents": ["129S1/Sv"],
                },
            ]
            for s in strains:
                cur.execute(
                    "INSERT INTO strains (name, equivalents) VALUES (?, ?)",
                    (s["name"], json.dumps(s["equivalents"])),
                )

        cur.execute("SELECT COUNT(*) AS c FROM cages")
        if cur.fetchone()["c"] == 0:
            cur.execute(
                "INSERT INTO cages (total_cages, mice_per_cage) VALUES (?, ?)",
                (20, 5),
            )


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


def parse_json_field(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return value


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
