"""Swedish dictation post-processing."""

from __future__ import annotations

import re


_COMMANDS = [
    ("nytt stycke", "\n\n"),
    ("ny rad", "\n"),
    ("radbrytning", "\n"),
    ("utropstecken", "!"),
    ("frågetecken", "?"),
    ("fragetecken", "?"),
    ("kommatecken", ","),
    ("komma", ","),
    ("punkt", "."),
    ("kolon", ":"),
    ("semikolon", ";"),
]


def post_process(text: str) -> str:
    """Apply deterministic Swedish dictation commands."""
    if not text:
        return ""

    processed = text.strip()
    processed = _apply_punctuation_commands(processed)
    processed = _clean_spacing(processed)
    return processed.strip()


def _apply_punctuation_commands(text: str) -> str:
    for phrase, replacement in _COMMANDS:
        pattern = re.compile(
            rf"(?<!\w){re.escape(phrase)}(?!\w)([,.;:!?])?",
            re.IGNORECASE,
        )
        text = pattern.sub(
            lambda match: match.group(0)
            if _is_literal_context(text, match.start())
            else replacement,
            text,
        )
    return text


def _clean_spacing(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"([,.;:!?])\s+([,.;:!?])", r"\2", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=\S)", r"\1 ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _is_literal_context(text: str, command_start: int) -> bool:
    """Return True when command words are being discussed as words."""
    prefix = text[:command_start].lower()
    sentence_start = max(
        prefix.rfind("."),
        prefix.rfind("!"),
        prefix.rfind("?"),
        prefix.rfind("\n"),
    )
    clause = prefix[sentence_start + 1 :]
    return bool(
        re.search(
            r"\b("
            r"saker som|"
            r"ord som|"
            r"orden|"
            r"ordet|"
            r"skriva|"
            r"säga|"
            r"sager|"
            r"heter|"
            r"kallas|"
            r"använda|"
            r"anvanda"
            r")\b",
            clause,
        )
    )
