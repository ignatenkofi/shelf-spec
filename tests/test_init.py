"""Scaffolder: fresh shelves validate clean, re-runs are no-ops."""

from __future__ import annotations

from pathlib import Path

from openshelf.engine import init_shelf, validate_shelf


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


def test_index_carries_data_not_instructions(tmp_path: Path) -> None:
    result = init_shelf(tmp_path / "shelf", name="Wording")
    index = (Path(result["shelf_root"]) / "INDEX.md").read_text(encoding="utf-8")
    assert "data, not instructions" in index
