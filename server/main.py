from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

load_dotenv()

DB_PATH = Path(os.getenv("DATABASE_PATH", "licenses.db"))
API_SECRET = os.getenv("LICENSE_API_SECRET", "")
app = FastAPI(title="Key System API", version="1.0.0")


def now() -> datetime:
    return datetime.now(timezone.utc)


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                key_hash TEXT PRIMARY KEY,
                key_type TEXT NOT NULL CHECK(key_type IN ('1d', 'lifetime')),
                created_at TEXT NOT NULL,
                expires_at TEXT,
                activated_at TEXT,
                device_id TEXT,
                revoked_at TEXT,
                created_by TEXT
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_license_device ON licenses(device_id) WHERE device_id IS NOT NULL")


init_db()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()


def check_secret(value: str | None) -> None:
    if not API_SECRET or not value or not hmac.compare_digest(value, API_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")


def make_key(prefix: str = "TWILIGHT") -> str:
    return f"{prefix}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"


class CreateLicense(BaseModel):
    key_type: str
    created_by: str | None = None


class ActivateRequest(BaseModel):
    key: str
    device_id: str


class RevokeRequest(BaseModel):
    key: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/admin/create")
def create_license(payload: CreateLicense, x_api_secret: str | None = Header(default=None)):
    check_secret(x_api_secret)
    if payload.key_type not in {"1d", "lifetime"}:
        raise HTTPException(400, "key_type must be 1d or lifetime")

    key = make_key()
    created = now()
    with db() as conn:
        conn.execute(
            "INSERT INTO licenses(key_hash,key_type,created_at,created_by) VALUES(?,?,?,?)",
            (hash_key(key), payload.key_type, created.isoformat(), payload.created_by),
        )
    # The plaintext key is returned only once; only its hash is stored.
    return {"key": key, "type": payload.key_type, "created_at": created.isoformat()}


@app.post("/activate")
def activate(payload: ActivateRequest):
    if not payload.device_id or len(payload.device_id) > 200:
        raise HTTPException(400, "Invalid device_id")

    key_hash = hash_key(payload.key)
    with db() as conn:
        row = conn.execute("SELECT * FROM licenses WHERE key_hash=?", (key_hash,)).fetchone()
        if row is None:
            raise HTTPException(404, "Invalid key")
        if row["revoked_at"]:
            raise HTTPException(403, "Key revoked")

        if row["device_id"] and row["device_id"] != payload.device_id:
            raise HTTPException(403, "Key is already bound to another installation")

        current = now()
        if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) <= current:
            raise HTTPException(403, "Key expired")

        if not row["device_id"]:
            expires = current + timedelta(days=1) if row["key_type"] == "1d" else None
            conn.execute(
                "UPDATE licenses SET device_id=?, activated_at=?, expires_at=? WHERE key_hash=? AND device_id IS NULL",
                (payload.device_id, current.isoformat(), expires.isoformat() if expires else None, key_hash),
            )
            row = conn.execute("SELECT * FROM licenses WHERE key_hash=?", (key_hash,)).fetchone()

        return {
            "valid": True,
            "type": row["key_type"],
            "device_id": row["device_id"],
            "activated_at": row["activated_at"],
            "expires_at": row["expires_at"],
        }


@app.post("/admin/revoke")
def revoke(payload: RevokeRequest, x_api_secret: str | None = Header(default=None)):
    check_secret(x_api_secret)
    with db() as conn:
        cur = conn.execute(
            "UPDATE licenses SET revoked_at=? WHERE key_hash=? AND revoked_at IS NULL",
            (now().isoformat(), hash_key(payload.key)),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Key not found or already revoked")
    return {"revoked": True}


@app.get("/admin/list")
def list_licenses(x_api_secret: str | None = Header(default=None)):
    check_secret(x_api_secret)
    with db() as conn:
        rows = conn.execute(
            "SELECT key_type,created_at,expires_at,activated_at,device_id,revoked_at,created_by FROM licenses ORDER BY created_at DESC"
        ).fetchall()
    return {"licenses": [dict(row) for row in rows]}
