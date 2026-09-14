from __future__ import annotations

import json
import uuid
from pathlib import Path

import httpx

DEFAULT_ID_FILE = Path.home() / ".twilight_key_installation"


def installation_id(path: Path = DEFAULT_ID_FILE) -> str:
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    value = str(uuid.uuid4())
    path.write_text(value + "\n", encoding="utf-8")
    return value

class LicenseError(RuntimeError):
    pass

def activate(base_url: str, key: str, id_file: Path = DEFAULT_ID_FILE) -> dict:
    device_id = installation_id(id_file)
    try:
        response = httpx.post(
            base_url.rstrip("/") + "/activate",
            json={"key": key, "device_id": device_id},
            timeout=15,
        )
    except httpx.HTTPError as exc:
        raise LicenseError("License server unavailable") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Activation failed")
        except json.JSONDecodeError:
            detail = "Activation failed"
        raise LicenseError(detail)
    return response.json()
