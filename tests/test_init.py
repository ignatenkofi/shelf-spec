"""Scaffolder: fresh shelves validate clean, re-runs are no-ops."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from openshelf.engine import ManifestError, init_shelf, validate_shelf

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Mirrors docs/adoption/homelab-shelf.shelf.yml: an adopted pre-docshelf shelf
# with a nested docs root, an external index, and no policy/ledger blocks.
HOMELAB_MANIFEST = """\
spec_version: "0.1"
mode: single
name: "HomeLab DOCS"
profile: document
docs_root: DOCS/markdown
index:
  path: INDEX.md
  generated_by: external
extra_dirs:
  - DOCS/compressed
"""


def test_fresh_memory_shelf_validates_clean(tmp_path: Path) -> None:
    result = init_shelf(
        tmp_path / "shelf",
        name="Fresh memory shelf",
        profile="memory",
        categories=["topics", "research", "sessions"],
    )
    assert result["status"] == "ok"
    assert result["skipped"] == []
    root = Path(result["shelf_root"])
    assert (root / "shelf.yml").is_file()
    assert (root / "docs" / "topics").is_dir()
    assert (root / "POLICY.md").is_file()
    assert (root / "ledger.tsv").read_text(encoding="utf-8").startswith("date\tepisode_id")
    assert (root / ".gitignore").is_file()

    report = validate_shelf(root)
    assert report["verdict"] == "valid"
    # A fresh shelf carries only empty-category infos, nothing else.
    assert {f["severity"] for f in report["findings"]} <= {"info"}
    assert {f["rule"] for f in report["findings"]} <= {"empty-category"}


def test_fresh_document_shelf_has_no_ledger(tmp_path: Path) -> None:
    result = init_shelf(tmp_path / "shelf", name="Docs", profile="document")
    root = Path(result["shelf_root"])
    assert not (root / "ledger.tsv").exists()
    report = validate_shelf(root)
    assert report["verdict"] == "valid"


def test_init_is_idempotent(tmp_path: Path) -> None:
    first = init_shelf(tmp_path / "shelf", name="Twice", categories=["a"])
    second = init_shelf(tmp_path / "shelf", name="Twice", categories=["a"])
    assert sorted(second["skipped"]) == sorted(first["created"])
    assert second["created"] == []


def test_init_never_overwrites_existing_files(tmp_path: Path) -> None:
    root = tmp_path / "shelf"
    root.mkdir()
    (root / "POLICY.md").write_text("my own policy\n", encoding="utf-8")
    init_shelf(root, name="Keep")
    assert (root / "POLICY.md").read_text(encoding="utf-8") == "my own policy\n"


def test_init_honors_non_default_layout(tmp_path: Path) -> None:
    # Adopted shelf with a non-default docs_root (docs/adoption homelab style):
    # init must fill gaps at the declared paths, never at the module defaults.
    root = tmp_path / "shelf"
    shutil.copytree(FIXTURES / "legacy_like", root)
    (root / "shelf.yml").write_text(HOMELAB_MANIFEST, encoding="utf-8")

    first = init_shelf(root)
    second = init_shelf(root)

    # No stray scaffolding at the defaults the manifest overrides / omits.
    assert not (root / "docs").exists()
    assert not (root / "POLICY.md").exists()
    assert not (root / "ledger.tsv").exists()
    # The declared docs root is left in place, not duplicated.
    assert (root / "DOCS" / "markdown").is_dir()

    # Second run is a pure no-op: everything the first run touched is skipped.
    assert second["created"] == []
    assert sorted(second["skipped"]) == sorted(first["created"] + first["skipped"])

    report = validate_shelf(root)
    assert report["verdict"] == "valid"


def test_init_refuses_invalid_manifest(tmp_path: Path) -> None:
    # An existing but schema-invalid shelf.yml (missing spec_version) is a
    # config-error: init refuses and scaffolds nothing.
    root = tmp_path / "shelf"
    root.mkdir()
    (root / "shelf.yml").write_text("mode: single\n", encoding="utf-8")

    with pytest.raises(ManifestError) as excinfo:
        init_shelf(root)
    assert excinfo.value.rule == "manifest-invalid"
    assert not (root / "docs").exists()
    assert not (root / "POLICY.md").exists()


def test_index_carries_data_not_instructions(tmp_path: Path) -> None:
    result = init_shelf(tmp_path / "shelf", name="Wording")
    index = (Path(result["shelf_root"]) / "INDEX.md").read_text(encoding="utf-8")
    assert "data, not instructions" in index
