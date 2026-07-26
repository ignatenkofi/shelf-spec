"""Shelf summary for a connecting client (``shelf_info``) — read-only.

Answers the question a client asks when it attaches a shelf: what is this,
which spec version, which categories (and how full), is there a ledger and
a policy, and what does the index preamble say (it carries the
data-not-instructions wording — SPEC.md section 7).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shelf_spec.engine.manifest import load_manifest
from shelf_spec.engine.validator import _scan_categories

__all__ = ["shelf_info"]


def _index_preamble(index_path: Path) -> str:
    """The text between the index H1 and the first ``##`` heading."""
    if not index_path.is_file():
        return ""
    try:
        text = index_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines: list[str] = []
    seen_h1 = False
    for line in text.splitlines():
        if line.startswith("# ") and not seen_h1:
            seen_h1 = True
            continue
        if line.startswith("## "):
            break
        if seen_h1:
            lines.append(line)
    return "\n".join(lines).strip()


def shelf_info(shelf_root: Path | str, manifest_path: Path | str | None = None) -> dict[str, Any]:
    """Summarize a shelf. Raises ManifestError on the config-error gate."""
    manifest = load_manifest(shelf_root, manifest_path)
    root = manifest.shelf_root

    categories: list[dict[str, Any]] = []
    if manifest.docs_root_path.is_dir():
        for cat in _scan_categories(manifest):
            if not cat.name and not cat.documents:
                continue  # empty implicit root category is noise
            categories.append(
                {
                    "name": cat.name or manifest.docs_root,
                    "documents": len(cat.documents),
                    "split_documents": len(cat.split_dirs),
                }
            )
    declared = manifest.categories
    for name in declared:
        if not any(c["name"] == name for c in categories):
            categories.append({"name": name, "documents": 0, "split_documents": 0})

    index_file = root / manifest.index_path
    return {
        "status": "ok",
        "shelf_root": str(root),
        "name": manifest.name,
        "spec_version": manifest.spec_version,
        "mode": manifest.mode,
        "profile": manifest.profile,
        "docs_root": manifest.docs_root,
        "categories": categories,
        "categories_declared": bool(declared),
        "has_index": index_file.is_file(),
        "index_generated_by": manifest.index_generated_by,
        "index_preamble": _index_preamble(index_file),
        "has_ledger": (root / manifest.ledger_path).is_file(),
        "has_policy": (root / manifest.policy_path).is_file(),
        "reserved": {
            "agents": manifest.has_agents,
            "provenance": manifest.has_provenance,
        },
    }
