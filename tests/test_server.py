"""MCP surface: tools accept flat keyword arguments (no 'params' envelope).

Regression guard for the wrapped-model footgun: when a tool takes a single
pydantic model argument, FastMCP nests the whole input under one key and a
hand-written client calling ``{"shelf_path": ...}`` gets a pydantic
"Field required" error back as tool text. The signatures must stay flat.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from shelf_spec.server import mcp


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call a tool through the server's validation path and parse the JSON reply.

    mcp 2.x returns a ``CallToolResult`` here; 1.x returned the content blocks
    (sometimes wrapped in a tuple). Only the 2.x shape is handled — the pin is
    ``mcp>=2.0.0,<3``, and accepting both would leave a branch no test covers.
    """
    result = asyncio.run(mcp.call_tool(name, arguments))
    assert not result.is_error, result.content
    text = result.content[0].text  # type: ignore[union-attr]
    return json.loads(text)


def test_input_schemas_are_flat() -> None:
    # `input_schema`, not `inputSchema`: mcp 2.x renamed the Tool fields to
    # snake_case. The flatness this test guards is a deliberate contract —
    # clients get named arguments, not a nested `params` object.
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert set(tools) == {"shelf_init", "shelf_validate", "shelf_info"}
    for tool in tools.values():
        properties = tool.input_schema["properties"]
        assert "params" not in properties, f"{tool.name} nests input under 'params'"
        assert "shelf_path" in properties
    assert "manifest_path" in tools["shelf_validate"].input_schema["properties"]
    assert {"name", "mode", "profile", "categories"} <= set(
        tools["shelf_init"].input_schema["properties"]
    )


def test_flat_call_shelf_validate(memshelf_like: Path) -> None:
    report = _call("shelf_validate", {"shelf_path": str(memshelf_like)})
    assert report["verdict"] == "valid"


def test_flat_call_shelf_info(memshelf_like: Path) -> None:
    info = _call("shelf_info", {"shelf_path": str(memshelf_like)})
    assert info["profile"] == "memory"


def test_flat_call_shelf_init(tmp_path: Path) -> None:
    root = tmp_path / "fresh"
    payload = _call(
        "shelf_init",
        {"shelf_path": str(root), "name": "Flat args", "profile": "memory"},
    )
    assert payload["status"] == "ok"
    assert (root / "shelf.yml").is_file()
    # Defaults still apply when optional arguments are omitted entirely.
    report = _call("shelf_validate", {"shelf_path": str(root)})
    assert report["verdict"] == "valid"


def test_config_error_still_reported_as_json(tmp_path: Path) -> None:
    report = _call("shelf_validate", {"shelf_path": str(tmp_path)})
    assert report["verdict"] == "config-error"
    assert report["findings"][0]["rule"] == "manifest-missing"
    # shelf_info raises ManifestError in the engine; the tool maps it to an
    # error response instead of scaffolding anything.
    info = _call("shelf_info", {"shelf_path": str(tmp_path)})
    assert info["status"] == "error"
    assert info["verdict"] == "config-error"
