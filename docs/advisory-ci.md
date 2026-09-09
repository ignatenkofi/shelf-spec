# CI stage for shelf repos — `shelf-spec validate --ci`

Drop-in GitHub Actions job for any shelf repository (memory or document).
Blocking by default: a spec violation turns the run red. The portfolio
shelves (`main-memshelf`, `homelab-shelf`, `unevie-shelf`) and the
`docshelf-mcp` conformance job run it this way since 2026-09-09.

```yaml
name: shelf-validate

on:
  push:
    branches: [main]
  pull_request:

jobs:
  shelf-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install shelf-spec
        run: pip install "shelf-spec>=0.2,<0.3"

      - name: Validate shelf against shelf-spec
        run: shelf-spec validate --ci .
```

Pin by minor: the spec is v0 and a new minor may add rules. Bumping the pin
is a deliberate PR on the shelf, with the new findings visible in that PR's
run, rather than a surprise on an unrelated push.

## Advisory mode, and why it is opt-in

A newly adopted shelf may not be clean yet. To see the report without
blocking merges, add `continue-on-error: true` on the job. Do this
deliberately and for a bounded time: an advisory stage is a stage nobody
reads. `main-memshelf` ran advisory from 2026-07-28 and carried an
`episode-frontmatter-missing` error in every log from 2026-08-24 until the
stage was flipped to blocking on 2026-09-09 — the log said "violations" for
two weeks, the check said green, and green is what people look at.

## No credential is involved — on either route

`shelf-spec` is a public repository and the package is on PyPI, so both
ways to install it work from any repository's Actions with no secret:

- **Published release** (the job above): `pip install "shelf-spec>=0.2,<0.3"`.
  What a shelf should use — it validates against a known revision.
- **Tip of `main`**: `pip install "git+https://github.com/ignatenkofi/shelf-spec.git"`.
  For exactly one consumer: `docshelf-mcp`'s conformance job, which checks
  the reference implementation against the spec as it currently stands,
  not as it was last cut.

### What this page used to prescribe, and why it is gone

Until 2026-09-09 the repository was private. The tip route then needed a
fine-grained PAT (`SHELF_SPEC_TOKEN`, Contents:read), and every consuming
job carried a `HAVE_TOKEN` gate on every step, because an ungated job under
`continue-on-error` with an expired PAT stays green while the validate
step never runs — a shelf that "looks covered" while nothing is checked.

Four repositories carried that token (`docshelf-mcp`, `main-memshelf`,
`homelab-shelf`, `unevie-shelf`). With the repository public the gate has
nothing to guard, so the secret was deleted from all four and the jobs
reduced to the shape above. The lesson stands even though the mechanism is
gone: a token that exists is a token that can leak, expire, or be
over-scoped, and the cheapest version of all three problems is not
issuing it. If a private fork ever brings the PAT back, bring the gate
back with it, on every step, not as an instruction to "wire the token
first".

## Exit contract

Exit codes: `0` conforms (warnings allowed; `--strict` promotes warnings
to failure), `1` spec violations, `2` config-error (no or invalid
`shelf.yml`; checked before any rule). The `--ci` flag prints the full JSON
report, so findings are machine-collectable from the log.

For a shelf that does not yet commit its `shelf.yml`, validate against a
candidate manifest kept elsewhere:

```bash
shelf-spec validate --ci --manifest path/to/candidate.shelf.yml .
```
