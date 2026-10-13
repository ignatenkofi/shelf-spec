"""The release workflow publishes only behind its gate (tag == __version__, lint, tests).

release.yml runs on a tag push and on a manual dispatch, ci.yml on push/PR:
nothing else stands between a ref and PyPI, so the gate job, the ``needs``
chain, the tag-ref condition on the publishing jobs and the wheel smoke test
in ``build`` are the whole contract. Whether the gate actually goes red on a
mismatched tag is a thing only a real tag push shows; this file pins the
wiring that makes it possible and simulates the ``if:`` conditions over the
refs a run can start from.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
import yaml

from tests.conftest import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

TAG_CHECK = "Tag matches package version"
SMOKE = "Smoke-test the wheel outside the checkout"


def _jobs() -> dict[str, Any]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _step(steps: list[dict[str, Any]], name: str) -> dict[str, Any]:
    """The step called ``name``.

    Raises if there is none, so a renamed/removed step fails loudly instead
    of comparing two empty lists.
    """
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(f"no step named {name!r}")


def _run_lines(step: dict[str, Any]) -> list[str]:
    """Non-blank, stripped lines of a step's ``run:`` script."""
    return [line.strip() for line in step["run"].splitlines() if line.strip()]


def _lint_commands(steps: list[dict[str, Any]]) -> list[str]:
    """Non-blank lines of the "Lint with ruff" step's ``run:`` script."""
    return _run_lines(_step(steps, "Lint with ruff"))


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


# --- publishing runs on tag refs only (shelf-spec#61) -------------------------
#
# A manual run (workflow_dispatch) from a branch went all the way to PyPI: the
# tag == __version__ check is skipped off a tag ref, and nothing else in the
# workflow looked at the ref. The simulator evaluates the workflow's own
# `if:` strings the way GitHub documents them (docs.github.com/en/actions/
# reference/workflows-and-actions/ — expressions, workflow-syntax,
# events-that-trigger-workflows, variables): `startsWith` is not case
# sensitive, an `if:` without a status function carries an implicit
# `success()`, a job whose `needs` failed or was skipped is skipped, and a
# manual run's `github.ref` is the branch or tag it was started from,
# `refs/heads/<branch>` or `refs/tags/<tag>`. A condition it does not model
# is refused, not guessed.

_STARTS_WITH_REF = re.compile(
    r"\s*(?:\$\{\{\s*)?startsWith\(\s*github\.ref\s*,\s*'([^']*)'\s*\)\s*(?:\}\}\s*)?"
)


def _if_holds(condition: str | None, ref: str) -> bool:
    if condition is None:
        return True
    match = _STARTS_WITH_REF.fullmatch(condition)
    if match is None:
        raise AssertionError(f"if: {condition!r} is beyond this simulator; extend it first")
    return ref.lower().startswith(match.group(1).lower())


def _needs(job: dict[str, Any]) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


def _simulate(ref: str) -> dict[str, bool]:
    """Which jobs run for a run started on ``ref``, every step succeeding.

    Also reports, under ``TAG_CHECK``, whether the gate's tag == __version__
    step runs.
    """
    jobs = _jobs()
    ran: dict[str, bool] = {}
    while len(ran) < len(jobs):
        ready = [
            name
            for name, job in jobs.items()
            if name not in ran and all(need in ran for need in _needs(job))
        ]
        assert ready, f"needs cycle or unknown job among {sorted(set(jobs) - set(ran))}"
        for name in ready:
            job = jobs[name]
            ran[name] = all(ran[need] for need in _needs(job)) and _if_holds(job.get("if"), ref)
    ran[TAG_CHECK] = ran["gate"] and _if_holds(
        _step(jobs["gate"]["steps"], TAG_CHECK).get("if"), ref
    )
    return ran


#: started as, github.ref -> does the tag check / build / publish-pypi /
#: github-release run. A manual run from a tag is the retry path: it still
#: publishes, behind the same tag check as a tag push.
TRUTH_TABLE = [
    ("tag push", "refs/tags/v1.2.3", True, True, True, True),
    ("manual run from a tag", "refs/tags/v1.2.3", True, True, True, True),
    ("manual run from main", "refs/heads/main", False, True, False, False),
    ("manual run from a branch named v1.2.3", "refs/heads/v1.2.3", False, True, False, False),
]


@pytest.mark.parametrize(
    ("ref", "tag_check", "build", "publish", "release"),
    [row[1:] for row in TRUTH_TABLE],
    ids=[row[0] for row in TRUTH_TABLE],
)
def test_release_truth_table(
    ref: str, tag_check: bool, build: bool, publish: bool, release: bool
) -> None:
    ran = _simulate(ref)
    assert not ran["publish-pypi"] or ran[TAG_CHECK], "PyPI is reachable past the tag check"
    assert (ran[TAG_CHECK], ran["build"], ran["publish-pypi"], ran["github-release"]) == (
        tag_check,
        build,
        publish,
        release,
    )


def test_simulator_refuses_a_condition_it_does_not_model() -> None:
    assert _if_holds("${{ startsWith(github.ref, 'REFS/TAGS/') }}", "refs/tags/v1.2.3")
    with pytest.raises(AssertionError, match="beyond this simulator"):
        _if_holds("github.event_name == 'push'", "refs/tags/v1.2.3")


def test_build_smoke_tests_the_wheel_outside_the_checkout() -> None:
    """The built wheel is installed and run before anything can publish it (#61).

    ``twine check`` reads metadata only. The schema reaches the wheel only
    through force-include, and ``load_schema`` falls back to the checkout's
    ``spec/``, so tests in the checkout pass on a wheel without the schema.
    A venv outside the checkout with the wheel and nothing else meets the
    package as a PyPI user does.
    """
    steps = _jobs()["build"]["steps"]
    names = [step.get("name") for step in steps]
    assert SMOKE in names
    assert names.index("Build sdist + wheel") < names.index(SMOKE)
    assert names.index(SMOKE) < names.index("Upload build artifacts")

    step = _step(steps, SMOKE)
    assert "if" not in step and not step.get("continue-on-error"), "the smoke must gate the job"
    lines = _run_lines(step)
    assert "$RUNNER_TEMP" in "\n".join(lines), "the venv must live outside the checkout"

    installs = [line.split("pip install", 1)[1].split() for line in lines if "pip install" in line]
    assert installs, "the smoke step installs nothing"
    for args in installs:
        # The built wheel and nothing else: not `-e .`, not `.`, no extras.
        assert [arg for arg in args if not arg.startswith("-")] == ["dist/*.whl"], args

    for command in ("--version", "init", "validate --ci"):
        assert any(re.search(rf'/shelf-spec"? {re.escape(command)}(\s|$)', ln) for ln in lines), (
            f"the smoke does not run the venv's `shelf-spec {command}`"
        )
