"""CLI exit-code contract (0/1/2) and machine output."""

from __future__ import annotations

import json
from pathlib import Path

from shelf_spec.cli import main
from tests.conftest import legacy_manifest


def test_validate_valid_exits_0(memshelf_like: Path, capsys) -> None:
    assert main(["validate", str(memshelf_like)]) == 0


def test_validate_violations_exit_1(memshelf_like: Path, capsys) -> None:
    (memshelf_like / "docs" / "topics" / "2026-01-10-fixture-topic.md").write_text(
        "no frontmatter\n", encoding="utf-8"
    )
    assert main(["validate", str(memshelf_like)]) == 1


def test_validate_config_error_exit_2(tmp_path: Path, capsys) -> None:
    assert main(["validate", str(tmp_path)]) == 2


def test_validate_ci_emits_json(memshelf_like: Path, capsys) -> None:
    code = main(["validate", "--ci", str(memshelf_like)])
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "valid"
    assert report["findings"] == []


def test_validate_strict_promotes_warnings(memshelf_like: Path, capsys) -> None:
    # A stale meta entry is a warning: exit 0 normally, 1 under --strict.
    meta = memshelf_like / "docs" / "topics" / ".meta.json"
    meta.write_text('{"gone.md": {"title": "Gone", "description": ""}}', encoding="utf-8")
    assert main(["validate", str(memshelf_like)]) == 0
    assert main(["validate", "--strict", str(memshelf_like)]) == 1


def test_validate_strict_pins_known_revision(memshelf_like: Path, capsys) -> None:
    """SPEC 2.1: forward-compat warnings pass by default and fail under --strict.

    A shelf from a newer spec revision (unknown ``profile``, unknown episode
    ``kind``) is exit 0 for a plain ``validate`` — the format promises not to
    redline it — while ``--strict`` is the documented way for CI to pin the
    revision this validator implements, so the same shelf is exit 1 there.
    """
    manifest = memshelf_like / "shelf.yml"
    episode = memshelf_like / "docs" / "topics" / "2026-01-10-fixture-topic.md"

    # Unknown profile: only `profile-unknown` is reported.
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("profile: memory", "profile: experience"),
        encoding="utf-8",
    )
    assert main(["validate", "--ci", str(memshelf_like)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert {f["rule"] for f in report["findings"]} == {"profile-unknown"}
    assert main(["validate", "--strict", "--ci", str(memshelf_like)]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "valid"  # the report is unchanged; only the exit code is

    # Unknown kind inside the known memory profile: same shape one level down.
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("profile: experience", "profile: memory"),
        encoding="utf-8",
    )
    episode.write_text(
        episode.read_text(encoding="utf-8").replace("kind: topic", "kind: pitfall"),
        encoding="utf-8",
    )
    assert main(["validate", "--ci", str(memshelf_like)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert {f["rule"] for f in report["findings"]} == {"episode-kind-unknown"}
    assert main(["validate", "--strict", str(memshelf_like)]) == 1


def test_validate_external_manifest(legacy_like: Path, capsys) -> None:
    code = main(["validate", "--ci", "--manifest", str(legacy_manifest()), str(legacy_like)])
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "valid"
    # The external-manifest run must not have created a manifest in the tree.
    assert not (legacy_like / "shelf.yml").exists()


def test_init_then_validate_roundtrip(tmp_path: Path, capsys) -> None:
    shelf = tmp_path / "shelf"
    assert main(["init", str(shelf), "--name", "CLI shelf", "--profile", "memory",
                 "--categories", "topics,research"]) == 0
    assert main(["validate", str(shelf)]) == 0


def test_info_exit_codes(memshelf_like: Path, tmp_path: Path, capsys) -> None:
    assert main(["info", str(memshelf_like)]) == 0
    assert main(["info", str(tmp_path)]) == 2


def test_info_json(memshelf_like: Path, capsys) -> None:
    assert main(["info", "--json", str(memshelf_like)]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["name"] == "Fixture working memory shelf"
