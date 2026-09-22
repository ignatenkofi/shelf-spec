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


def _jobs() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def test_gate_compares_tag_with_version_and_runs_lint_and_tests() -> None:
    scripts = "\n".join(step.get("run", "") for step in _jobs()["gate"]["steps"])
    assert "shelf_spec.__version__" in scripts
    assert "GITHUB_REF_NAME" in scripts
    assert "ruff check src tests" in scripts
    assert "pytest" in scripts


def test_publish_chain_waits_for_the_gate() -> None:
    jobs = _jobs()
    assert jobs["build"]["needs"] == "gate"
    assert jobs["publish-pypi"]["needs"] == "build"
    assert jobs["github-release"]["needs"] == "publish-pypi"
