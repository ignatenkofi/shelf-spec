"""FastMCP server — thin transport over the engine (stdio).

Three tools, named per the spec surface (no vendor prefix):
``shelf_init`` (write, local), ``shelf_validate`` (read), ``shelf_info``
(read). Every tool returns a JSON string; tool logic lives in the engine so
it is unit-testable without MCP (pattern: docshelf-mcp server/tools split).

Tools take **flat keyword arguments** (``{"shelf_path": ...}`` in
``tools/call``), the argument style most MCP servers expose. FastMCP builds
the input schema straight from the signatures; per-parameter constraints
live in ``Annotated[..., Field(...)]`` metadata. Do not wrap parameters in
a single pydantic model — that nests everything under one ``params`` key
and breaks hand-written clients.

Validation and info never scaffold a shelf silently: a directory without a
manifest is a config-error (``shelf_validate``) or an error response
(``shelf_info``), mirroring docshelf-mcp's ``NotAShelfError`` guard.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from shelf_spec import __version__
from shelf_spec.config import default_shelf_root
from shelf_spec.engine import ManifestError, init_shelf, shelf_info, validate_shelf

__all__ = ["mcp", "main"]

logger = logging.getLogger("shelf_spec")

mcp = MCPServer("shelf-spec")


def _resolve_root(shelf_path: str | None) -> Path:
    return Path(shelf_path).expanduser().resolve() if shelf_path else default_shelf_root()


def _serialize(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _error_response(exc: Exception, tool: str) -> str:
    if isinstance(exc, ManifestError):
        logger.warning("%s: %s", tool, exc)
        return _serialize(
            {
                "status": "error",
                "verdict": "config-error",
                "rule": exc.rule,
                "error": exc.detail,
            }
        )
    logger.exception("%s failed", tool)
    return _serialize({"status": "error", "error": str(exc), "type": type(exc).__name__})


_ShelfPathInit = Annotated[
    str | None,
    Field(
        description="Shelf root to scaffold. Defaults to $SHELF_SPEC_ROOT or the "
        "server's working directory.",
    ),
]
_ShelfPathValidate = Annotated[
    str | None,
    Field(
        description="Shelf root to validate. Defaults to $SHELF_SPEC_ROOT or the "
        "server's working directory.",
    ),
]
_ShelfPathInfo = Annotated[
    str | None,
    Field(
        description="Shelf root to summarize. Defaults to $SHELF_SPEC_ROOT or the "
        "server's working directory.",
    ),
]


@mcp.tool(
    name="shelf_init",
    annotations={
        "title": "Scaffold a spec-conformant shelf",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def tool_shelf_init(
    shelf_path: _ShelfPathInit = None,
    name: Annotated[
        str,
        Field(
            description="Human-readable shelf name (stored in shelf.yml and the index H1).",
            max_length=200,
        ),
    ] = "",
    mode: Annotated[
        str,
        Field(
            description="Shelf mode: 'single' (all of v0) or 'multi' (reserved for M1).",
            pattern="^(single|multi)$",
        ),
    ] = "single",
    profile: Annotated[
        str,
        Field(
            description="Rule profile: 'memory' (episodes, ledger, policy) or 'document'.",
            pattern="^(memory|document)$",
        ),
    ] = "document",
    categories: Annotated[
        list[str],
        Field(description="Categories to pre-create under docs/ and declare in shelf.yml."),
    ] = [],  # noqa: B006 — read-only default; FastMCP validates a fresh list per call
) -> str:
    """Create a shelf skeleton: shelf.yml, docs root + categories, POLICY.md
    stub, minimal INDEX.md, .gitignore, and (memory profile) a ledger header.

    Idempotent — existing files are never overwritten; the response lists
    what was created and what was skipped.
    """
    try:
        payload = init_shelf(
            _resolve_root(shelf_path),
            name=name.strip(),
            mode=mode,
            profile=profile,
            categories=list(categories),
        )
        return _serialize(payload)
    except Exception as exc:
        return _error_response(exc, "shelf_init")


@mcp.tool(
    name="shelf_validate",
    annotations={
        "title": "Validate a shelf against shelf-spec",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def tool_shelf_validate(
    shelf_path: _ShelfPathValidate = None,
    manifest_path: Annotated[
        str | None,
        Field(
            description="Optional external shelf.yml candidate: validate the tree "
            "against this manifest without requiring (or touching) one inside the shelf.",
        ),
    ] = None,
) -> str:
    """Lint a shelf tree against shelf-spec v0.

    Returns a report with verdict ('valid' | 'violations' | 'config-error')
    and findings (rule, severity, path, detail, suggested_fix). Read-only —
    nothing is fixed or scaffolded.
    """
    try:
        payload = validate_shelf(_resolve_root(shelf_path), manifest_path)
        return _serialize(payload)
    except Exception as exc:
        return _error_response(exc, "shelf_validate")


@mcp.tool(
    name="shelf_info",
    annotations={
        "title": "Summarize a shelf for a connecting client",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def tool_shelf_info(shelf_path: _ShelfPathInfo = None) -> str:
    """Manifest + index summary: name, spec version, mode, profile,
    categories with counts, ledger/policy presence, the index preamble
    (which carries the data-not-instructions wording), and which reserved
    M1 fields are present.
    """
    try:
        payload = shelf_info(_resolve_root(shelf_path))
        return _serialize(payload)
    except Exception as exc:
        return _error_response(exc, "shelf_info")


def _build_parser() -> argparse.ArgumentParser:
    # Пользовательский вход — `shelf-spec serve` (README, и он же в конфиге
    # клиента); этот парсер виден только тому, кто зовёт модуль напрямую.
    # Команды `shelf-spec-server` не существует: в [project.scripts] ровно
    # одна запись, `shelf-spec`. Имя, которого нет, — тот же дефект, что и
    # `openshelf` до него, поэтому prog называет реально работающий вызов.
    parser = argparse.ArgumentParser(
        prog="python -m shelf_spec.server",
        description="shelf-spec MCP server (stdio); обычный вход — shelf-spec serve",
    )
    parser.add_argument("--version", action="version", version=f"shelf-spec {__version__}")
    parser.add_argument(
        "--shelf",
        default="",
        help="Default shelf root (sets SHELF_SPEC_ROOT before starting).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the stdio MCP server (also: ``shelf-spec serve``)."""
    args = _build_parser().parse_args(argv)
    if args.shelf:
        os.environ["SHELF_SPEC_ROOT"] = args.shelf
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logger.info("Starting shelf-spec MCP server %s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
