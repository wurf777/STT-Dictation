"""Local dictation history for learning from raw and processed text."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

import config

_last_record_id: Optional[str] = None


def log_dictation(
    *,
    raw_text: str,
    processed_text: str,
    output_text: str,
    duration_seconds: Optional[float] = None,
    output_mode: Optional[str] = None,
    segments: Optional[list[dict]] = None,
    words: Optional[list[dict]] = None,
    pauses: Optional[list[dict]] = None,
) -> Optional[str]:
    """Append one dictation record to the local JSONL history."""
    global _last_record_id

    if not config.get("dictation_learning_enabled"):
        return None

    raw_text = (raw_text or "").strip()
    processed_text = (processed_text or "").strip()
    output_text = (output_text or "").strip()
    if not raw_text and not processed_text and not output_text:
        return None

    path = _history_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    record_id = str(uuid4())
    record = {
        "id": record_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "raw_text": raw_text,
        "processed_text": processed_text,
        "output_text": output_text,
        "corrected_text": None,
        "duration_seconds": round(duration_seconds, 3)
        if duration_seconds is not None
        else None,
        "segments": segments or [],
        "words": words or [],
        "pauses": pauses or [],
        "output_mode": output_mode or config.get("output_mode"),
        "language": config.get("language"),
    }

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        _last_record_id = record_id
        return record_id
    except OSError as e:
        print(f"[learning] Kunde inte spara diktathistorik: {e}")
        return None


def get_last_dictation() -> Optional[dict]:
    """Return the most recent dictation record from history."""
    records = _read_records()
    for record in reversed(records):
        if record.get("raw_text") or record.get("processed_text"):
            return record
    return None


def save_correction(corrected_text: str, record_id: Optional[str] = None) -> bool:
    """Save corrected text on the selected or latest dictation record."""
    corrected_text = (corrected_text or "").strip()
    if not corrected_text:
        return False

    records = _read_records()
    if not records:
        return False

    target_id = record_id or _last_record_id
    target_index = None

    if target_id:
        for index, record in enumerate(records):
            if record.get("id") == target_id:
                target_index = index
                break

    if target_index is None:
        for index in range(len(records) - 1, -1, -1):
            if records[index].get("raw_text") or records[index].get("processed_text"):
                target_index = index
                break

    if target_index is None:
        return False

    records[target_index]["corrected_text"] = corrected_text
    records[target_index]["corrected_at"] = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    return _write_records(records)


def _history_path() -> str:
    configured = config.get("dictation_history_path")
    return config.resolve_app_path(configured)


def _read_records() -> list[dict]:
    path = _history_path()
    if not os.path.exists(path):
        return []

    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError as e:
        print(f"[learning] Kunde inte läsa diktathistorik: {e}")
    return records


def _write_records(records: list[dict]) -> bool:
    path = _history_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError as e:
        print(f"[learning] Kunde inte uppdatera diktathistorik: {e}")
        return False
