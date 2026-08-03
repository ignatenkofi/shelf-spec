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
        run: pip install shelf-spec

      - name: Validate shelf against shelf-spec
        run: shelf-spec validate --ci .
```

## The package is on PyPI — the install step needs no credential

`pip install shelf-spec` works from any repository's Actions with no secret at
all: **shelf-spec 0.1.0 is published**. Verified end to end rather than assumed
— installed from PyPI into a bare venv, then `shelf-spec validate --ci` run
against a real memory shelf, which answered `verdict: valid`.

That makes the job above the whole story: no `SHELF_SPEC_TOKEN`, no
`HAVE_TOKEN` gate, no silent-no-op hazard to guard against, because there is
no credential whose absence could turn the stage into a green pass that
validated nothing.

### What this section used to say, and why it was wrong

Until 2026-08-04 this document prescribed a fine-grained PAT, on the reasoning
that `shelf-spec` is a private repository and "publishing is gated on the
final-name decision (#3) — not available yet". The naming decision landed
(ADR 0007, the `openshelf` → `shelf-spec` rename), the package was published,
and this page was not updated. Four consuming repositories are still carrying
a `SHELF_SPEC_TOKEN` secret they no longer need for this purpose.

The lesson is the one this page is otherwise about: a stale instruction keeps
a credential alive. A token that exists is a token that can leak,
expire, or be over-scoped, and the cheapest version of all three problems is
not issuing it.

**State of the consumers as of 2026-08-04.** `sqst-memshelf`, `homelab-shelf`
and `unevie-shelf` still install from git with `SHELF_SPEC_TOKEN` and the
`HAVE_TOKEN` gate — they were wired that way hours before this section was
corrected. Nothing is broken there; the gate does its job. Switching them to
`pip install shelf-spec` is a deliberate choice with a real trade-off
(validate against the published release, or against tip), so it belongs to
whoever maintains those shelves, not to this page. Until then, read the job
above as what a *new* shelf should copy, not as a description of what the
existing three do.

### When you still want the git route

Installing from the repository still makes sense in exactly one case: you want
to validate against **tip** rather than the published release — e.g.
`docshelf-mcp`'s conformance job, which checks the reference implementation
against the spec as it currently stands, not as it was last cut. Then the PAT
is unavoidable while the repository is private, and the job needs the
`HAVE_TOKEN` gate below, because a missing or expired credential otherwise
produces an orange run that validated nothing:

```yaml
    continue-on-error: true
    env:
      HAVE_TOKEN: ${{ secrets.SHELF_SPEC_TOKEN != '' }}
    steps:
      - name: No SHELF_SPEC_TOKEN — honest skip
        if: env.HAVE_TOKEN != 'true'
        run: echo "::notice::SHELF_SPEC_TOKEN is not set — the shelf was NOT validated."

      # ... every other step also gated on env.HAVE_TOKEN == 'true'
      - name: Install shelf-spec from tip
        if: env.HAVE_TOKEN == 'true'
        run: pip install "git+https://x-access-token:${{ secrets.SHELF_SPEC_TOKEN }}@github.com/ignatenkofi/shelf-spec.git"
```

Gating every step, rather than telling the reader to "wire the token first",
is deliberate: that instruction covers the moment the job is added and nothing
after it, and a fine-grained PAT expires. On the day it does, an ungated job
stays green (job-level `continue-on-error`), the validate step never executes,
and no signal is emitted anywhere.

Residual, deliberately not gated: an install failure for any *other* reason
(network, a broken package) still goes orange without failing the run, same as
any advisory stage. The gate separates "no credential" from "the check ran";
it does not turn the advisory job into a blocking one.

Exit codes: `0` conforms (warnings allowed), `1` spec violations, `2`
config-error (no or invalid `shelf.yml`). The `--ci` flag prints the full
JSON report, so findings are machine-collectable from the log.

For a shelf that does not yet commit its `shelf.yml`, validate against a
candidate manifest kept elsewhere:

```bash
shelf-spec validate --ci --manifest path/to/candidate.shelf.yml .
```
