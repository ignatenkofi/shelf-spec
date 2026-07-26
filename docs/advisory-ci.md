# Advisory CI stage for shelf repos — `shelf-spec validate --ci`

Drop-in GitHub Actions job for any shelf repository (memory or document).
Advisory: `continue-on-error` keeps the shelf's own workflow green while
the report is visible in the job log. Flip it to blocking once the shelf
has a committed `shelf.yml` and a clean run.

```yaml
name: shelf-validate

on:
  push:
    branches: [main]
  pull_request:

jobs:
  shelf-validate:
    runs-on: ubuntu-latest
    # Advisory while the spec is v0: report, do not block.
    continue-on-error: true
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install shelf-spec
        run: pip install "git+https://x-access-token:${{ secrets.OPENSHELF_TOKEN }}@github.com/ignatenkofi/shelf-spec.git"

      - name: Validate shelf against shelf-spec
        run: shelf-spec validate --ci .
```

## While this repo is private, the install step needs a token

`shelf-spec` is a private repository, and a workflow's default `GITHUB_TOKEN`
is scoped to **its own** repo — it cannot read this one. A plain
`pip install "git+https://github.com/ignatenkofi/shelf-spec.git"` from another
repository's Actions therefore fails at the install step.

This interacts badly with `continue-on-error: true`: the job goes orange, the
validate step never runs, and the shelf looks covered while **nothing is
being validated**. A silent no-op is worse than no stage at all, so wire the
token before adding the job, not after.

Two working routes:

1. **Fine-grained PAT** (works today, owner-gated — a PAT is a credential):
   Contents:read on `shelf-spec` only, saved as the `SHELF_SPEC_TOKEN` secret
   in *each* consuming shelf repo. That is the form shown above.
2. **Wait for PyPI** — once the package publishes, the step collapses to
   `pip install shelf-spec` with no secret anywhere. Publishing is gated on
   the final-name decision (#3), so this is the cleaner end state but not
   available yet.

If neither is in place, hold off on the stage: an honest missing check beats
a green-looking one that never ran.

Exit codes: `0` conforms (warnings allowed), `1` spec violations, `2`
config-error (no or invalid `shelf.yml`). The `--ci` flag prints the full
JSON report, so findings are machine-collectable from the log.

For a shelf that does not yet commit its `shelf.yml`, validate against a
candidate manifest kept elsewhere:

```bash
shelf-spec validate --ci --manifest path/to/candidate.shelf.yml .
```
