import json
import os
import tempfile

import config
from correction_window import _format_diff
from learning_suggestions import add_to_learning_basket, suggest_replacements


def test_suggests_short_replacement_from_correction():
    suggestions = suggest_replacements(
        "Jag ska spela in t-rort eller i morgon.",
        "Jag ska spela in Terort elle? i morgon.",
    )

    assert {"from": "t-rort eller", "to": "Terort elle?"} in [
        {"from": item["from"], "to": item["to"]} for item in suggestions
    ]


def test_skips_identical_text():
    assert suggest_replacements("Hej dar.", "Hej dar.") == []


def test_suggests_only_changed_words_in_long_sentence():
    raw = (
        "Så för ett tag sedan så konstaterade jag att Matsum numera kör "
        "chatt-GBT och han älskar det. Jag tror att han är villig att betala "
        "för det också numera."
    )
    corrected = (
        "Så för ett tag sedan så konstaterade jag att Masum numera kör "
        "ChatGPT och han älskar det. Jag tror att han är villig att betala "
        "för det också numera."
    )

    pairs = [
        {"from": item["from"], "to": item["to"]}
        for item in suggest_replacements(raw, corrected)
    ]

    assert pairs == [
        {"from": "Matsum", "to": "Masum"},
        {"from": "chatt-GBT", "to": "ChatGPT"},
    ]


def test_diff_shows_only_changed_spans():
    raw = "Jag gillar chatt-GBT och Matsum."
    corrected = "Jag gillar ChatGPT och Masum."

    diff = _format_diff(raw, corrected)

    assert diff == [
        "- chatt-GBT",
        "+ ChatGPT",
        "- Matsum",
        "+ Masum",
    ]
    assert "Jag" not in diff
    assert "gillar" not in diff
    assert "och" not in diff


def test_adds_candidate_to_learning_basket():
    old_path = config.get("learning_basket_path")
    with tempfile.TemporaryDirectory() as tmp:
        basket_path = os.path.join(tmp, "basket.jsonl")
        config.set("learning_basket_path", basket_path)
        try:
            ok = add_to_learning_basket(
                {"from": "t-rort eller", "to": "Terort elle?"},
                raw_text="Nästa program blir t-rort eller",
                corrected_text="Nästa program blir Terort elle?",
                record_id="abc",
            )
            assert ok
            with open(basket_path, "r", encoding="utf-8") as f:
                item = json.loads(f.readline())
            assert item["status"] == "pending"
            assert item["type"] == "replacement"
            assert item["from"] == "t-rort eller"
            assert item["to"] == "Terort elle?"
            assert item["record_id"] == "abc"
        finally:
            config.set("learning_basket_path", old_path)
