"""Saves uploaded damage photos to disk, organized by report."""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import UPLOADS_DIR


def save_upload(report_id: int, part: str, filename: str | None, raw_bytes: bytes) -> Path:
    suffix = Path(filename).suffix if filename else ""
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,5}", suffix or ""):
        suffix = ".jpg"  # unrecognized/missing extension — content is still validated as an image upstream

    report_dir = UPLOADS_DIR / str(report_id)
    report_dir.mkdir(parents=True, exist_ok=True)

    safe_part = re.sub(r"[^A-Za-z0-9_-]+", "_", part).strip("_") or "part"
    dest = report_dir / f"{safe_part}_{uuid.uuid4().hex[:8]}{suffix}"
    dest.write_bytes(raw_bytes)
    return dest
