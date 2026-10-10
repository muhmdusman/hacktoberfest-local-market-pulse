"""Tests for app/agents/jsonio.py"""

import pytest
from langchain_core.messages import AIMessage

from app.agents.jsonio import parse_json_object, reply_text


def test_parses_object_inside_fences_and_chatter():
    text = 'Here you go:\n```json\n{"a": {"b": "}"}, "c": 1}\n```\nThanks'
    assert parse_json_object(text) == {"a": {"b": "}"}, "c": 1}


@pytest.mark.parametrize("text", ["", "no json here", '{"a": 1', "[1, 2]"])
def test_rejects_missing_or_broken_json(text):
    with pytest.raises(ValueError):
        parse_json_object(text)


def test_reply_text_handles_messages_and_strings():
    assert reply_text(AIMessage(content="hi")) == "hi"
    assert reply_text("raw") == "raw"
