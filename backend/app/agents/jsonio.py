"""Pull the first JSON object out of a model reply (tolerates fences and chatter)."""

import json
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    """Return the first balanced {...} in `text` as a dict, else raise ValueError."""
    text = text or ""
    start = text.find("{")
    if start == -1:
        raise ValueError("no JSON object in reply")

    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                obj = json.loads(text[start : i + 1])  # JSONDecodeError is a ValueError
                if not isinstance(obj, dict):
                    raise ValueError("JSON reply is not an object")
                return obj
    raise ValueError("unbalanced JSON object in reply")


def reply_text(reply: Any) -> str:
    """Text content of a LangChain message (content can be str or blocks)."""
    content = getattr(reply, "content", reply)
    return content if isinstance(content, str) else json.dumps(content)
