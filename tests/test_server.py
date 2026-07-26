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
    """Call a tool through FastMCP's validation path and parse the JSON reply."""
    result = asyncio.run(mcp.call_tool(name, arguments))
    blocks = result[0] if isinstance(result, tuple) else result
    text = blocks[0].text  # type: ignore[union-attr]
    return json.loads(text)


def test_input_schemas_are_flat() -> None:
    tools = {t.name: t for t in asyncio.run(mcp.list_tools())}
    assert set(tools) == {"shelf_init", "shelf_validate", "shelf_info"}
    for tool in tools.values():
        properties = tool.inputSchema["properties"]
        assert "params" not in properties, f"{tool.name} nests input under 'params'"
        assert "shelf_path" in properties
    assert "manifest_path" in tools["shelf_validate"].inputSchema["properties"]
    assert {"name", "mode", "profile", "categories"} <= set(
        tools["shelf_init"].inputSchema["properties"]
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
