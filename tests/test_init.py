"""Scaffolder: fresh shelves validate clean, re-runs are no-ops."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

import shelf_spec.engine.initializer as initializer_module
from shelf_spec.engine import ManifestError, init_shelf, validate_shelf
from shelf_spec.engine.manifest import load_schema

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Mirrors the adopted homelab manifest (hardware-shelf/shelf.yml in homelab-iac,
# ex docs/adoption/homelab-shelf.shelf.yml): an adopted pre-docshelf shelf
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
    # Compare exact names: on case-insensitive filesystems (macOS APFS)
    # (root / "docs").exists() is True because the fixture's DOCS matches.
    entries = {p.name for p in root.iterdir()}
    assert "docs" not in entries
    assert "POLICY.md" not in entries
    assert "ledger.tsv" not in entries
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


def _tree(base: Path) -> list[str]:
    return sorted(str(p.relative_to(base)) for p in base.rglob("*"))


# The shelf sits two levels below tmp_path, so "../../escaped" resolves to
# tmp_path/nest/escaped: outside the shelf root, still inside tmp_path. An
# empty tmp_path afterwards therefore means nothing was written anywhere —
# no shelf root, no shelf.yml, no directory where the name points.
# Duplicates are refused (schema uniqueItems), not silently deduplicated.
@pytest.mark.parametrize(
    "category",
    ["../../escaped", "a/b", "{tmp}/abs_target", "a,a"],
    ids=["traversal", "nested", "absolute", "duplicate"],
)
def test_init_refuses_invalid_categories_before_any_write(tmp_path: Path, category: str) -> None:
    categories = category.format(tmp=tmp_path).split(",")
    with pytest.raises(ManifestError) as excinfo:
        init_shelf(tmp_path / "nest" / "shelf", categories=categories)
    assert excinfo.value.rule == "manifest-invalid"
    assert "categories" in excinfo.value.detail
    assert _tree(tmp_path) == []


@pytest.mark.parametrize("category", ["../../escaped", "a/b"], ids=["traversal", "nested"])
def test_init_on_existing_shelf_refuses_invalid_category(tmp_path: Path, category: str) -> None:
    # Implicit categories (none declared), so the refusal comes from the
    # schema gate on the requested names, not from the declared-list check.
    root = tmp_path / "nest" / "shelf"
    init_shelf(root)
    before = _tree(tmp_path)
    with pytest.raises(ManifestError) as excinfo:
        init_shelf(root, categories=[category])
    assert excinfo.value.rule == "manifest-invalid"
    assert _tree(tmp_path) == before


def test_init_on_existing_shelf_refuses_undeclared_category(tmp_path: Path) -> None:
    # The manifest declares its categories: init fills only what it declares,
    # a docs/zz it does not would fail validate with category-undeclared.
    root = tmp_path / "shelf"
    init_shelf(root, categories=["topics"])
    before = _tree(tmp_path)
    with pytest.raises(ManifestError) as excinfo:
        init_shelf(root, categories=["topics", "zz"])
    assert excinfo.value.rule == "manifest-invalid"
    assert "zz" in excinfo.value.detail
    assert _tree(tmp_path) == before
    assert validate_shelf(root)["verdict"] == "valid"


def test_init_on_implicit_shelf_adds_category(tmp_path: Path) -> None:
    # No categories declared = implicit (any directory is one), so a new
    # schema-valid name is still created and the shelf still validates.
    root = tmp_path / "shelf"
    init_shelf(root)
    result = init_shelf(root, categories=["newcat"])
    assert result["created"] == ["docs/newcat/"]
    assert (root / "docs" / "newcat").is_dir()
    assert validate_shelf(root)["verdict"] == "valid"


def test_containment_check_backs_up_the_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Defence in depth: with the category pattern gone from the schema (a
    # looser revision, or a Windows path the '/'-only pattern does not know),
    # the resolve() check alone still refuses a name that leaves docs_root.
    schema = copy.deepcopy(load_schema())
    del schema["properties"]["categories"]["items"]["pattern"]
    monkeypatch.setattr(initializer_module, "load_schema", lambda: schema)
    with pytest.raises(ManifestError) as excinfo:
        init_shelf(tmp_path / "nest" / "shelf", categories=["../../escaped"])
    assert "outside the docs root" in excinfo.value.detail
    assert _tree(tmp_path) == []
