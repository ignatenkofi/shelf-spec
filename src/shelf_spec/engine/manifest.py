"""Locate, parse, and schema-validate ``shelf.yml``.

The manifest is the conformance gate: a missing, unparseable, or
schema-invalid manifest is a **config-error** and no other operation runs
against the shelf (SPEC.md section 3, exit code 2). That contract lives in
:class:`ManifestError` — every caller that resolves a shelf goes through
:func:`load_manifest` first.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

import jsonschema
import yaml

__all__ = [
    "MANIFEST_FILENAME",
    "Manifest",
    "ManifestError",
    "load_manifest",
    "load_schema",
]

MANIFEST_FILENAME = "shelf.yml"

#: Manifest defaults (SPEC.md section 3 / shelf.schema.json descriptions).
DEFAULT_DOCS_ROOT = "docs"
DEFAULT_INDEX_PATH = "INDEX.md"
DEFAULT_GENERATED_BY = "docshelf-mcp"
DEFAULT_LEDGER_PATH = "ledger.tsv"
DEFAULT_POLICY_PATH = "POLICY.md"
DEFAULT_PROFILE = "document"


class ManifestError(Exception):
    """The manifest failed the config-error gate.

    ``rule`` is one of ``manifest-missing`` / ``manifest-invalid`` — the
    same identifiers the validator reports and SPEC.md section 9.1 names.
    """

    def __init__(self, rule: str, detail: str) -> None:
        super().__init__(detail)
        self.rule = rule
        self.detail = detail


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    """Load ``shelf.schema.json``.

    The canonical copy lives at ``spec/shelf.schema.json`` in the repo; the
    wheel ships a copy inside the package (see pyproject force-include). Try
    the packaged copy first, then fall back to the repo-relative path so an
    editable install works without a build step.
    """
    candidates = []
    try:
        packaged = resources.files("shelf_spec").joinpath("spec/shelf.schema.json")
        if packaged.is_file():
            candidates.append(packaged.read_text(encoding="utf-8"))
    except (OSError, TypeError):  # pragma: no cover - packaging edge
        pass
    if not candidates:
        repo_copy = Path(__file__).resolve().parents[3] / "spec" / "shelf.schema.json"
        if repo_copy.is_file():
            candidates.append(repo_copy.read_text(encoding="utf-8"))
    if not candidates:  # pragma: no cover - broken install
        raise FileNotFoundError(
            "shelf.schema.json not found (neither packaged nor at spec/shelf.schema.json)"
        )
    return json.loads(candidates[0])


@dataclass
class Manifest:
    """Parsed and schema-valid ``shelf.yml`` with defaults applied."""

    shelf_root: Path
    manifest_path: Path
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def spec_version(self) -> str:
        return self.raw["spec_version"]

    @property
    def mode(self) -> str:
        return self.raw["mode"]

    @property
    def name(self) -> str:
        return self.raw.get("name", "")

    @property
    def profile(self) -> str:
        return self.raw.get("profile", DEFAULT_PROFILE)

    @property
    def docs_root(self) -> str:
        return self.raw.get("docs_root", DEFAULT_DOCS_ROOT)

    @property
    def docs_root_path(self) -> Path:
        return self.shelf_root / self.docs_root

    @property
    def categories(self) -> list[str]:
        return list(self.raw.get("categories") or [])

    @property
    def index_path(self) -> str:
        return (self.raw.get("index") or {}).get("path", DEFAULT_INDEX_PATH)

    @property
    def index_generated_by(self) -> str:
        return (self.raw.get("index") or {}).get("generated_by", DEFAULT_GENERATED_BY)

    @property
    def ledger_path(self) -> str:
        return (self.raw.get("ledger") or {}).get("path", DEFAULT_LEDGER_PATH)

    @property
    def policy_path(self) -> str:
        return (self.raw.get("policy") or {}).get("path", DEFAULT_POLICY_PATH)

    @property
    def extra_dirs(self) -> list[str]:
        return list(self.raw.get("extra_dirs") or [])

    @property
    def has_agents(self) -> bool:
        return "agents" in self.raw

    @property
    def has_provenance(self) -> bool:
        return "provenance" in self.raw


def load_manifest(shelf_root: Path | str, manifest_path: Path | str | None = None) -> Manifest:
    """Load and schema-validate the manifest for ``shelf_root``.

    Args:
        shelf_root: Shelf directory the manifest describes.
        manifest_path: Explicit manifest file. When given, the shelf tree is
            validated against this *external* candidate — the shelf itself is
            not touched and needs no ``shelf.yml`` of its own (CLI
            ``--manifest``). Defaults to ``<shelf_root>/shelf.yml``.

    Raises:
        ManifestError: rule ``manifest-missing`` when the file does not
            exist; rule ``manifest-invalid`` when it does not parse as YAML,
            is not a mapping, or fails shelf.schema.json.
    """
    shelf_root = Path(shelf_root).expanduser().resolve()
    path = (
        Path(manifest_path).expanduser().resolve()
        if manifest_path is not None
        else shelf_root / MANIFEST_FILENAME
    )
    if not path.is_file():
        raise ManifestError(
            "manifest-missing",
            f"no manifest at {path}; a shelf must have a shelf.yml "
            "(run 'shelf-spec init' to scaffold one, or pass --manifest)",
        )

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError("manifest-invalid", f"shelf.yml does not parse as YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError(
            "manifest-invalid",
            f"shelf.yml must be a YAML mapping, got {type(data).__name__}",
        )

    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        details = "; ".join(
            f"{'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
            for err in errors
        )
        raise ManifestError("manifest-invalid", f"shelf.yml fails shelf.schema.json: {details}")

    return Manifest(shelf_root=shelf_root, manifest_path=path, raw=data)
