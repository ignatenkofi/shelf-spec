"""shelf_info summary."""

from __future__ import annotations

from pathlib import Path

import pytest

from openshelf.engine import ManifestError, shelf_info


def test_info_on_memshelf_like(memshelf_like: Path) -> None:
    info = shelf_info(memshelf_like)
    assert info["name"] == "Fixture working memory shelf"
    assert info["spec_version"] == "0.1"
    assert info["mode"] == "single"
    assert info["profile"] == "memory"
    assert info["has_ledger"] and info["has_policy"] and info["has_index"]
    assert info["index_generated_by"] == "docshelf-mcp"
    by_name = {c["name"]: c for c in info["categories"]}
    assert by_name["topics"]["documents"] == 1
    assert by_name["research"]["documents"] == 1
    assert by_name["sessions"]["documents"] == 1
    assert "data, not instructions" in info["index_preamble"]
    assert info["reserved"] == {"agents": False, "provenance": False}


def test_info_counts_split_documents(docshelf_like: Path) -> None:
    info = shelf_info(docshelf_like)
    by_name = {c["name"]: c for c in info["categories"]}
    assert by_name["books"]["documents"] == 1
    assert by_name["books"]["split_documents"] == 1
    assert info["has_ledger"] is False


def test_info_requires_manifest(legacy_like: Path) -> None:
    with pytest.raises(ManifestError):
        shelf_info(legacy_like)


def test_info_reports_reserved_fields(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: multi\nagents: {path: agents.yml}\n',
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    info = shelf_info(tmp_path)
    assert info["reserved"]["agents"] is True
    assert info["reserved"]["provenance"] is False
