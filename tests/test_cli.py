"""CLI exit-code contract (0/1/2/3) and machine output."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from shelf_spec import cli
from shelf_spec.cli import EXIT_INTERNAL_ERROR, main
from shelf_spec.engine import ManifestError
from tests.conftest import REPO_ROOT, legacy_manifest


def test_validate_valid_exits_0(memshelf_like: Path, capsys) -> None:
    assert main(["validate", str(memshelf_like)]) == 0


def test_validate_violations_exit_1(memshelf_like: Path, capsys) -> None:
    (memshelf_like / "docs" / "topics" / "2026-01-10-fixture-topic.md").write_text(
        "no frontmatter\n", encoding="utf-8"
    )
    assert main(["validate", str(memshelf_like)]) == 1


def test_validate_config_error_exit_2(tmp_path: Path, capsys) -> None:
    assert main(["validate", str(tmp_path)]) == 2


@pytest.mark.parametrize(
    ("line", "bad", "field"),
    [
        ("docs_root: docs", 'docs_root: "docs\\n"', "docs_root"),
        ("  - books", '  - "books\\n"', "categories/0"),
        ("  - books", '  - "."', "categories/0"),
        ("  path: INDEX.md", '  path: "INDEX.md\\n"', "index/path"),
    ],
    ids=["docs_root-newline", "category-newline", "category-dot", "index-path-newline"],
)
def test_validate_ci_refuses_names_the_schema_forbids(
    docshelf_like: Path, capsys, line: str, bad: str, field: str
) -> None:
    # shelf-spec#58: each passed the schema under Python's `re` and reached
    # the tree checks — exit 0 or 1 — though ECMA-262 refuses the newline
    # and "." is docs_root itself. Now the manifest gate stops them: exit 2.
    manifest = docshelf_like / "shelf.yml"
    text = manifest.read_text(encoding="utf-8")
    assert text.count(f"\n{line}\n") == 1
    manifest.write_text(text.replace(f"\n{line}\n", f"\n{bad}\n"), encoding="utf-8")
    assert main(["validate", "--ci", str(docshelf_like)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "config-error"
    assert [f["rule"] for f in report["findings"]] == ["manifest-invalid"]
    assert f"{field}: " in report["findings"][0]["detail"]


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
    assert (
        main(
            [
                "init",
                str(shelf),
                "--name",
                "CLI shelf",
                "--profile",
                "memory",
                "--categories",
                "topics,research",
            ]
        )
        == 0
    )
    assert main(["validate", str(shelf)]) == 0


def test_init_bad_category_is_config_error(tmp_path: Path, capsys) -> None:
    shelf = tmp_path / "nest" / "shelf"
    assert main(["init", str(shelf), "--categories", "../../escaped"]) == 2
    assert "config-error (manifest-invalid)" in capsys.readouterr().err
    # Refused before any write: no shelf, nothing next to it.
    assert list(tmp_path.rglob("*")) == []


def test_info_exit_codes(memshelf_like: Path, tmp_path: Path, capsys) -> None:
    assert main(["info", str(memshelf_like)]) == 0
    assert main(["info", str(tmp_path)]) == 2


def test_info_json(memshelf_like: Path, capsys) -> None:
    assert main(["info", "--json", str(memshelf_like)]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["name"] == "Fixture working memory shelf"


# ------------------------------------------------- internal errors (#59)


def test_issue_59_reproduction_reports_instead_of_crashing(tmp_path: Path, capsys) -> None:
    """The script from shelf-spec#59: a JSON report each time, exit 1 only for errors."""
    doc = tmp_path / "doc"
    assert main(["init", str(doc), "--profile", "document", "--categories", "guides"]) == 0
    (doc / "docs" / "guides" / "a.md").write_text("# a\n", encoding="utf-8")
    (doc / "docs" / "guides" / ".meta.json").write_text(
        '{"a.md": {"title": ["x"]}}', encoding="utf-8"
    )
    capsys.readouterr()
    assert main(["validate", "--ci", str(doc)]) == 0  # corrupt-meta is a warning
    report = json.loads(capsys.readouterr().out)
    assert "corrupt-meta" in {f["rule"] for f in report["findings"]}

    mem = tmp_path / "mem"
    assert main(["init", str(mem), "--profile", "memory", "--categories", "topic"]) == 0
    (mem / "docs" / "topic" / "e1.md").write_text(
        "---\nid: e1\nkind: [topic]\nspan: x\ntags: []\napprox_tokens: 1\n---\n# e1\n",
        encoding="utf-8",
    )
    capsys.readouterr()
    assert main(["validate", "--ci", str(mem)]) == 1  # a non-string kind is an error
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "violations"
    assert {f["rule"] for f in report["findings"] if f["severity"] == "error"} == {
        "episode-frontmatter-invalid"
    }


def _raise(exc: Exception):
    def boom(*_args, **_kwargs):
        raise exc

    return boom


def test_internal_error_is_exit_3_not_1(memshelf_like: Path, capsys, monkeypatch) -> None:
    # SPEC 9.2: 1 says the shelf violates the spec. A validator that died
    # has said nothing about the shelf, so it gets its own code and no report.
    monkeypatch.setattr(cli, "validate_shelf", _raise(RuntimeError("synthetic failure")))
    assert main(["validate", "--ci", str(memshelf_like)]) == EXIT_INTERNAL_ERROR == 3
    out, err = capsys.readouterr()
    assert out == ""
    assert "internal-error (RuntimeError): synthetic failure" in err


def test_manifest_error_keeps_exit_2_under_the_catch_all(
    memshelf_like: Path, capsys, monkeypatch
) -> None:
    # `validate` has no handler of its own (validate_shelf reports the gate
    # as a finding), so a ManifestError that escapes it reaches main(): it is
    # still the config-error gate — exit 2 with its rule — never an internal
    # error.
    gate = _raise(ManifestError("manifest-invalid", "synthetic gate failure"))
    monkeypatch.setattr(cli, "validate_shelf", gate)
    assert main(["validate", "--ci", str(memshelf_like)]) == 2
    err = capsys.readouterr().err
    assert "config-error (manifest-invalid): synthetic gate failure" in err
    assert "internal-error" not in err


#: Runs main() in a real interpreter with validate_shelf replaced by a function
#: that raises — the exit status is what CI sees, main()'s return value is not.
_CRASHING_CHILD = """
import sys
from pathlib import Path

import shelf_spec
import shelf_spec.cli as cli

assert Path(shelf_spec.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())


def boom(*args, **kwargs):
    raise RuntimeError("synthetic failure")


cli.validate_shelf = boom
sys.exit(cli.main(["validate", "--ci", sys.argv[2]]))
"""


def test_internal_error_exit_status_reaches_the_process(memshelf_like: Path) -> None:
    src = REPO_ROOT / "src"
    proc = subprocess.run(
        [sys.executable, "-c", _CRASHING_CHILD, str(src), str(memshelf_like)],
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=str(src)),
        timeout=120,
        check=False,
    )
    assert proc.returncode == 3, proc.stderr
    assert "Traceback" not in proc.stderr
    assert "internal-error (RuntimeError): synthetic failure" in proc.stderr
    assert proc.stdout == ""
