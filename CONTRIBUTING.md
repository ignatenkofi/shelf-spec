# Contributing to shelf-spec

shelf-spec is a **format** first and a validator second. Most changes to
the format do not start here: they start in the implementations that write
shelves — [memshelf-mcp](https://github.com/ignatenkofi/memshelf-mcp) and
[docshelf-mcp](https://github.com/ignatenkofi/docshelf-mcp) — and in the
live shelves they manage. This file exists mostly to keep those two in
step.

## The one rule: a format change opens an issue here

A pull request in memshelf-mcp or docshelf-mcp that changes **what a
conforming shelf looks like on disk** — a manifest key, a frontmatter
field, a file the tool now writes or renders, a directory it now creates,
a column of `ledger.tsv`, a required section of an episode, who writes a
derived file and when — opens an issue in this repository **before or
together with** that PR, and the PR links it. The issue names the change,
the shelves it is already live on, and whether the spec should describe it
(ADR 0005: the spec follows the shelves) or declare it implementation-
defined. Closing the issue means `spec/SPEC.md` says one or the other.

The spec drifted from the shelves for a season without this rule
(shelf-spec#55: the derived ledger, `archive/` and rollups, retention —
all shipped in memshelf-mcp, none described here until the audit found
them). The rule costs one issue per format change and removes that class
of drift.

What does **not** need an issue here: tool behaviour that leaves the
on-disk shelf unchanged (ranking, reports, dry runs, adapters, CLI flags),
bug fixes that bring a tool back to what the spec already says, and
documentation.

## Changing the spec

- `spec/SPEC.md` is normative prose; `spec/shelf.schema.json` is the
  normative field list for `shelf.yml`. Change both when a manifest key
  changes, and add or adjust an example under `spec/examples/`.
- Every validator rule the engine emits is listed in SPEC section 9.1
  with its severity. A new `Finding` rule in `src/shelf_spec/engine/`
  lands with its 9.1 entry, a negative fixture that makes it fire and a
  positive one that keeps it quiet.
- v0 is descriptive (ADR 0005): where the document and the reference
  implementations disagree, the document is clarified. Record the
  decision in `CHANGELOG.md` under `Unreleased`; a design decision gets an
  ADR in `adr/`.
- Versioning is semver on the document (SPEC section 11): an editorial
  revision that changes no on-disk contract bumps the minor version;
  an incompatible format change bumps the major. Package releases follow
  `src/shelf_spec/__init__.py` and `CHANGELOG.md`; tags are the owner's.

## Checking a change locally

CI (`.github/workflows/ci.yml`) runs on GitHub-hosted runners for every
push and PR; the same commands work on a laptop:

```bash
pip install -e ".[dev]"      # or: uv run --extra dev ...
ruff check .
ruff format --check .
python -c "import mcp"       # the stdio test skips silently without the SDK
pytest -q
```

A change to the spec or the validator is also checked against the live
shelves it describes — the validator's promise is that an existing shelf
stays conformant (SPEC section 3). With the shelves cloned next to this
repository:

```bash
shelf-spec validate --ci ../main-memshelf
shelf-spec validate --ci ../memshelf-mcp/shelf
```

Both must answer exit 0 with no new findings; an info finding that was
there before the change is not new. Mention the result in the PR body,
including when a shelf could not be reached from where the check ran.

## Submitting a pull request

1. Branch off `main`; keep the PR to one concern.
2. Reference the issue (`Refs #N`, or `Closes #N` when the PR resolves it
   entirely).
3. Add the `CHANGELOG.md` entry under `Unreleased`.
4. Say in the PR body what you ran and what you could not run.

Merges, tags and PyPI releases are the owner's actions.
