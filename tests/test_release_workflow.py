"""The release workflow publishes only behind its gate (tag == __version__, lint, tests).

release.yml runs on tag push, ci.yml on push/PR: nothing else stands between
a tag and PyPI, so the gate job and the ``needs`` chain are the whole
contract. Whether the gate actually goes red on a mismatched tag is a thing
only a real tag push shows; this file pins the wiring that makes it possible.
"""

from __future__ import annotations

from typing import Any

import yaml

from tests.conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _jobs() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _lint_commands(steps: list[dict[str, Any]]) -> list[str]:
    """Non-blank lines of the "Lint with ruff" step's ``run:`` script.

    Raises if no such step exists, so a renamed/removed step fails loudly
    instead of comparing two empty lists.
    """
    for step in steps:
        if step.get("name") == "Lint with ruff":
            return [line.strip() for line in step["run"].splitlines() if line.strip()]
    raise AssertionError("no step named 'Lint with ruff'")


def test_gate_compares_tag_with_version_and_runs_lint_and_tests() -> None:
    scripts = "\n".join(step.get("run", "") for step in _jobs()["gate"]["steps"])
    assert "shelf_spec.__version__" in scripts
    assert "GITHUB_REF_NAME" in scripts
    assert "pytest" in scripts


def test_gate_lint_matches_ci_workflow() -> None:
    """The release gate must lint exactly as strictly as ci.yml.

    shelf-spec#51: the gate used to run only ``ruff check src tests`` —
    narrower than ci.yml and missing ``ruff format --check`` entirely, so a
    tag could reach PyPI with code ci.yml would have rejected on every push
    or PR. Comparing against ci.yml's own step (instead of hardcoding a
    second copy of the commands here) means the two can't quietly drift
    apart again: a literal in this test would just be another place for
    that to happen unnoticed.
    """
    ci_lint = _lint_commands(
        yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))["jobs"]["test"]["steps"]
    )
    # Sanity check that ci.yml's step was actually parsed, not some
    # unrelated/empty step — the commands themselves are ci.yml's contract.
    assert "ruff check ." in ci_lint
    assert "ruff format --check ." in ci_lint

    gate_lint = _lint_commands(_jobs()["gate"]["steps"])
    assert gate_lint == ci_lint


def test_publish_chain_waits_for_the_gate() -> None:
    jobs = _jobs()
    assert jobs["build"]["needs"] == "gate"
    assert jobs["publish-pypi"]["needs"] == "build"
    assert jobs["github-release"]["needs"] == "publish-pypi"
