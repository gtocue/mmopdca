"""Very small YAML helper used for tests.

This fallback parser supports only a subset of YAML syntax sufficient for the
project's sample files. It understands simple key/value mappings and inline
lists/dicts. The implementation is intentionally tiny to avoid external
dependencies when running in the minimal CI environment.
"""

import json
import re
from typing import Any


def _parse_value(val: str) -> Any:
    if val.startswith("[") and val.endswith("]"):
        return [_parse_value(v.strip()) for v in val[1:-1].split(";") if v.strip()] if ";" in val else [
            _parse_value(v.strip()) for v in val[1:-1].split(",") if v.strip()
        ]
    if val.startswith("{") and val.endswith("}"):
        out = {}
        for pair in val[1:-1].split(","):
            if not pair.strip():
                continue
            k, v = pair.split(":", 1)
            out[k.strip().strip("'\"")]=_parse_value(v.strip())
        return out
    if val.lower() in {"true", "false"}:
        return val.lower() == "true"
    if re.fullmatch(r"[-+]?[0-9]+", val):
        return int(val)
    if re.fullmatch(r"[-+]?[0-9]*\.[0-9]+", val):
        return float(val)
    return val.strip("'\"")


def safe_load(stream: Any):
    text = stream.decode() if isinstance(stream, bytes) else str(stream)
    result: dict[str, Any] = {}
    stack = [(0, result)]

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        key_part, _, val_part = raw.lstrip().partition(":")
        key = key_part.strip()
        val = val_part.strip()

        while stack and indent < stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError("Invalid indentation")
        container = stack[-1][1]
        if not val:
            new: dict[str, Any] = {}
            container[key] = new
            stack.append((indent + 2, new))
        else:
            container[key] = _parse_value(val)

    return result

    def safe_dump(data: Any, *_, **__):
    return json.dumps(data)
    