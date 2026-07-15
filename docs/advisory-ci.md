# Advisory CI stage for shelf repos — `openshelf validate --ci`

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

      - name: Install openshelf
        run: pip install "git+https://github.com/ignatenkofi/openshelf.git"

      - name: Validate shelf against shelf-spec
        run: openshelf validate --ci .
```

Exit codes: `0` conforms (warnings allowed), `1` spec violations, `2`
config-error (no or invalid `shelf.yml`). The `--ci` flag prints the full
JSON report, so findings are machine-collectable from the log.

For a shelf that does not yet commit its `shelf.yml`, validate against a
candidate manifest kept elsewhere:

```bash
openshelf validate --ci --manifest path/to/candidate.shelf.yml .
```
