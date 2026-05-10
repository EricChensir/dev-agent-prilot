from __future__ import annotations

from issuefix_agent.llm import extract_json_object


def test_extract_plain_json() -> None:
    assert extract_json_object('{"summary":"ok"}') == {"summary": "ok"}


def test_extract_fenced_json() -> None:
    text = '```json\n{"summary":"ok", "plan": []}\n```'
    assert extract_json_object(text)["summary"] == "ok"


def test_extract_json_with_prefix() -> None:
    text = 'Here is the result: {"summary":"ok"}'
    assert extract_json_object(text) == {"summary": "ok"}
