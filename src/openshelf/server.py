"""FastMCP server — thin transport over the engine (stdio).

Three tools, named per the spec surface (no vendor prefix):
``shelf_init`` (write, local), ``shelf_validate`` (read), ``shelf_info``
(read). Every tool returns a JSON string; tool logic lives in the engine so
it is unit-testable without MCP (pattern: docshelf-mcp server/tools split).

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

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from openshelf import __version__
from openshelf.config import default_shelf_root
from openshelf.engine import ManifestError, init_shelf, shelf_info, validate_shelf

__all__ = ["mcp", "main"]

logger = logging.getLogger("openshelf")

mcp = FastMCP("openshelf")


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


class _BaseInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


class ShelfInitInput(_BaseInput):
    """Input for ``shelf_init``."""

    shelf_path: str | None = Field(
        default=None,
        description="Shelf root to scaffold. Defaults to $OPENSHELF_ROOT or the "
        "server's working directory.",
    )
    name: str = Field(
        default="",
        description="Human-readable shelf name (stored in shelf.yml and the index H1).",
        max_length=200,
    )
    mode: str = Field(
        default="single",
        description="Shelf mode: 'single' (all of v0) or 'multi' (reserved for M1).",
        pattern="^(single|multi)$",
    )
    profile: str = Field(
        default="document",
        description="Rule profile: 'memory' (episodes, ledger, policy) or 'document'.",
        pattern="^(memory|document)$",
    )
    categories: list[str] = Field(
        default_factory=list,
        description="Categories to pre-create under docs/ and declare in shelf.yml.",
    )


class ShelfValidateInput(_BaseInput):
    """Input for ``shelf_validate``."""

    shelf_path: str | None = Field(
        default=None,
        description="Shelf root to validate. Defaults to $OPENSHELF_ROOT or the "
        "server's working directory.",
    )
    manifest_path: str | None = Field(
        default=None,
        description="Optional external shelf.yml candidate: validate the tree "
        "against this manifest without requiring (or touching) one inside the shelf.",
    )


class ShelfInfoInput(_BaseInput):
    """Input for ``shelf_info``."""

    shelf_path: str | None = Field(
        default=None,
        description="Shelf root to summarize. Defaults to $OPENSHELF_ROOT or the "
        "server's working directory.",
    )


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
def tool_shelf_init(params: ShelfInitInput) -> str:
    """Create a shelf skeleton: shelf.yml, docs root + categories, POLICY.md
    stub, minimal INDEX.md, .gitignore, and (memory profile) a ledger header.

    Idempotent — existing files are never overwritten; the response lists
    what was created and what was skipped.
    """
    try:
        payload = init_shelf(
            _resolve_root(params.shelf_path),
            name=params.name,
            mode=params.mode,
            profile=params.profile,
            categories=params.categories,
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
def tool_shelf_validate(params: ShelfValidateInput) -> str:
    """Lint a shelf tree against shelf-spec v0.

    Returns a report with verdict ('valid' | 'violations' | 'config-error')
    and findings (rule, severity, path, detail, suggested_fix). Read-only —
    nothing is fixed or scaffolded.
    """
    try:
        payload = validate_shelf(_resolve_root(params.shelf_path), params.manifest_path)
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
def tool_shelf_info(params: ShelfInfoInput) -> str:
    """Manifest + index summary: name, spec version, mode, profile,
    categories with counts, ledger/policy presence, the index preamble
    (which carries the data-not-instructions wording), and which reserved
    M1 fields are present.
    """
    try:
        payload = shelf_info(_resolve_root(params.shelf_path))
        return _serialize(payload)
    except Exception as exc:
        return _error_response(exc, "shelf_info")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openshelf-server", description="openshelf MCP server (stdio)"
    )
    parser.add_argument("--version", action="version", version=f"openshelf {__version__}")
    parser.add_argument(
        "--shelf",
        default="",
        help="Default shelf root (sets OPENSHELF_ROOT before starting).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for the stdio MCP server (also: ``openshelf serve``)."""
    args = _build_parser().parse_args(argv)
    if args.shelf:
        os.environ["OPENSHELF_ROOT"] = args.shelf
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    logger.info("Starting openshelf MCP server %s", __version__)
    mcp.run()


if __name__ == "__main__":
    main()
