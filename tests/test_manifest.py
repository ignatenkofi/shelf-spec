"""Manifest loading and the config-error gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from shelf_spec.engine.manifest import ManifestError, load_manifest, load_schema
from tests.conftest import legacy_manifest


def test_load_valid_manifest(memshelf_like: Path) -> None:
    m = load_manifest(memshelf_like)
    assert m.spec_version == "0.1"
    assert m.mode == "single"
    assert m.profile == "memory"
    assert m.categories == ["topics", "research", "sessions"]
    assert m.index_generated_by == "docshelf-mcp"
    assert m.docs_root_path == memshelf_like / "docs"


def test_defaults_applied(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text('spec_version: "0.1"\nmode: single\n', encoding="utf-8")
    m = load_manifest(tmp_path)
    assert m.profile == "document"
    assert m.docs_root == "docs"
    assert m.index_path == "INDEX.md"
    assert m.index_generated_by == "docshelf-mcp"
    assert m.ledger_path == "ledger.tsv"
    assert m.policy_path == "POLICY.md"
    assert m.categories == []
    assert not m.has_agents and not m.has_provenance


def test_missing_manifest_is_config_error(tmp_path: Path) -> None:
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-missing"


def test_unparseable_yaml_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text("spec_version: [unclosed\n", encoding="utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"


def test_schema_violation_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: banana\n', encoding="utf-8"
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "banana" in exc.value.detail


def test_unknown_top_level_key_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\ntypo_field: 1\n', encoding="utf-8"
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"


def test_policy_patterns_accepted(tmp_path: Path) -> None:
    """``policy.patterns`` names the machine-readable pattern file (SPEC 4.5).

    memshelf-mcp writes it into every manifest it scaffolds; a schema that
    refused the key made every live memshelf shelf a config-error.
    """
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\n'
        "mode: single\n"
        "profile: memory\n"
        "policy:\n"
        "  path: POLICY.md\n"
        "  patterns: POLICY.patterns\n",
        encoding="utf-8",
    )
    m = load_manifest(tmp_path)
    assert m.policy_path == "POLICY.md"
    assert m.raw["policy"]["patterns"] == "POLICY.patterns"


def test_policy_patterns_escaping_path_is_config_error(tmp_path: Path) -> None:
    """Same path contract as ``policy.path``: relative to the root, no ``..``."""
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\npolicy:\n  patterns: ../POLICY.patterns\n',
        encoding="utf-8",
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "patterns" in exc.value.detail


def test_unknown_policy_key_is_config_error(tmp_path: Path) -> None:
    """Opening ``policy`` for ``patterns`` must not open it for typos."""
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\nmode: single\npolicy:\n  path: POLICY.md\n  typo_field: 1\n',
        encoding="utf-8",
    )
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "typo_field" in exc.value.detail


def test_missing_required_field_is_config_error(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text("mode: single\n", encoding="utf-8")
    with pytest.raises(ManifestError) as exc:
        load_manifest(tmp_path)
    assert exc.value.rule == "manifest-invalid"
    assert "spec_version" in exc.value.detail


def test_external_manifest_path(legacy_like: Path) -> None:
    m = load_manifest(legacy_like, legacy_manifest())
    assert m.shelf_root == legacy_like
    assert m.docs_root == "DOCS/markdown"
    assert m.index_generated_by == "external"
    assert m.extra_dirs == ["DOCS/compressed"]
    # The tree itself still has no manifest of its own.
    assert not (legacy_like / "shelf.yml").exists()


def test_reserved_fields_accepted(tmp_path: Path) -> None:
    (tmp_path / "shelf.yml").write_text(
        'spec_version: "0.1"\n'
        "mode: multi\n"
        "agents: {path: agents.yml}\n"
        "provenance: {dir: provenance/, required: true}\n",
        encoding="utf-8",
    )
    m = load_manifest(tmp_path)
    assert m.mode == "multi"
    assert m.has_agents and m.has_provenance


def test_schema_is_itself_valid() -> None:
    import jsonschema

    jsonschema.Draft202012Validator.check_schema(load_schema())
