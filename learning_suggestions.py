"""Suggest and approve simple learning rules from corrected dictations."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from uuid import uuid4

import config


_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def suggest_replacements(raw_text: str, corrected_text: str) -> list[dict]:
    """Return short replacement candidates from raw/corrected text pairs."""
    existing = {
        str(src).strip().lower()
        for src in (config.get("replacements") or {}).keys()
        if str(src).strip()
    }

    suggestions = []
    seen = set()
    for change in find_text_changes(raw_text, corrected_text):
        raw_phrase = change["from"]
        corrected_phrase = change["to"]
        if not _is_useful_candidate(raw_phrase, corrected_phrase):
            continue

        key = raw_phrase.lower()
        pair_key = (key, corrected_phrase.lower())
        if key in existing or pair_key in seen:
            continue

        seen.add(pair_key)
        suggestions.append(
            {
                "from": raw_phrase,
                "to": corrected_phrase,
                "reason": "Skillnad mellan Whisper-text och facit",
            }
        )

    return suggestions


def find_text_changes(raw_text: str, corrected_text: str) -> list[dict]:
    """Return changed spans only, never unchanged context words."""
    raw_tokens = _tokenize(raw_text)
    corrected_tokens = _tokenize(corrected_text)
    if not raw_tokens or not corrected_tokens:
        return []

    matcher = SequenceMatcher(
        None,
        _lower_tokens(raw_tokens),
        _lower_tokens(corrected_tokens),
        autojunk=False,
    )
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        raw_phrase = _untokenize(raw_tokens[i1:i2]).strip()
        corrected_phrase = _untokenize(corrected_tokens[j1:j2]).strip()
        if raw_phrase.lower() == corrected_phrase.lower():
            continue

        changes.append(
            {
                "from": raw_phrase,
                "to": corrected_phrase,
                "tag": tag,
            }
        )
    return changes


def approve_replacement(src: str, dst: str) -> bool:
    """Add one approved candidate to config replacements."""
    src = (src or "").strip()
    dst = (dst or "").strip()
    if not src or not dst or src.lower() == dst.lower():
        return False

    replacements = dict(config.get("replacements") or {})
    for existing_src in list(replacements.keys()):
        if str(existing_src).lower() == src.lower():
            del replacements[existing_src]
            break

    replacements[src] = dst
    config.set("replacements", replacements)
    config.save()
    print(f"[learning] Godkand regel: '{src}' -> '{dst}'")
    return True


def add_to_learning_basket(
    suggestion: dict,
    *,
    raw_text: str = "",
    corrected_text: str = "",
    record_id: str | None = None,
) -> bool:
    """Save one candidate for later review without activating it."""
    src = str(suggestion.get("from") or "").strip()
    dst = str(suggestion.get("to") or "").strip()
    if not _is_useful_candidate(src, dst):
        return False

    path = _basket_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    item = {
        "id": str(uuid4()),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pending",
        "type": "replacement",
        "from": src,
        "to": dst,
        "reason": suggestion.get("reason") or "Skillnad mellan Whisper-text och facit",
        "record_id": record_id,
        "raw_text": raw_text,
        "corrected_text": corrected_text,
    }

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[learning] Lade i larandekorg: '{src}' -> '{dst}'")
        return True
    except OSError as e:
        print(f"[learning] Kunde inte spara larandekorg: {e}")
        return False


def _basket_path() -> str:
    configured = config.get("learning_basket_path")
    return config.resolve_app_path(configured)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text or "")


def _lower_tokens(tokens: list[str]) -> list[str]:
    return [token.lower() for token in tokens]


def _untokenize(tokens: list[str]) -> str:
    text = ""
    no_space_before = set(".,!?;:%)]}-")
    no_space_after = set("([{-")
    for token in tokens:
        if not text:
            text = token
        elif token in no_space_before:
            text += token
        elif text[-1] in no_space_after:
            text += token
        else:
            text += " " + token
    return text


def _is_useful_candidate(raw_phrase: str, corrected_phrase: str) -> bool:
    if not raw_phrase or not corrected_phrase:
        return False
    if raw_phrase.lower() == corrected_phrase.lower():
        return False
    if len(raw_phrase) > 80 or len(corrected_phrase) > 80:
        return False

    raw_words = re.findall(r"\w+", raw_phrase, re.UNICODE)
    corrected_words = re.findall(r"\w+", corrected_phrase, re.UNICODE)
    if not raw_words or not corrected_words:
        return False
    if len(raw_words) > 8 or len(corrected_words) > 8:
        return False

    return True
