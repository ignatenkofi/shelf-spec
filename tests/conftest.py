"""Shared fixtures: repo paths and mutable copies of the on-disk mini-shelves."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def memshelf_like(tmp_path: Path) -> Path:
    """Mutable copy of the memory-profile mini-shelf."""
    dst = tmp_path / "memshelf_like"
    shutil.copytree(FIXTURES / "memshelf_like", dst)
    return dst


@pytest.fixture()
def docshelf_like(tmp_path: Path) -> Path:
    """Mutable copy of the document-profile mini-shelf."""
    dst = tmp_path / "docshelf_like"
    shutil.copytree(FIXTURES / "docshelf_like", dst)
    return dst


@pytest.fixture()
def legacy_like(tmp_path: Path) -> Path:
    """Mutable copy of the manifest-less legacy tree (homelab profile)."""
    dst = tmp_path / "legacy_like"
    shutil.copytree(FIXTURES / "legacy_like", dst)
    return dst


def legacy_manifest() -> Path:
    """External manifest candidate for the legacy tree."""
    return FIXTURES / "manifests" / "legacy_like.shelf.yml"
