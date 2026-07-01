import json
import os
import tempfile

import config
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
