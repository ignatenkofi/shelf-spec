# Adoption kit — shelf.yml candidates for the owner's shelves

Ready-to-apply `shelf.yml` manifests for the three existing shelves named
in the M0 roadmap. Each one makes its shelf spec-conformant by adding a
single file (`mode: single`, compatibility promise of ADR-0005) — nothing
else migrates.

| candidate | target shelf | profile | notes |
|---|---|---|---|
| `sqst-memshelf.shelf.yml` | sqst-memshelf | memory | ledger + policy declared |
| `unevie-shelf.shelf.yml` | unevie-shelf | document | older `.docshelf.json` stays valid |
| `homelab-shelf.shelf.yml` | homelab-shelf | document | pre-docshelf: nested docs root, external index, extra dirs |

All three validate green (`exit 0`, zero error findings) against the live
clones via the external-manifest mode, which needs no write access to the
shelf:

```bash
openshelf validate --ci --manifest docs/adoption/<shelf>.shelf.yml /path/to/<shelf>
```

## Status: drafted, not yet applied

Committing these files **into the shelf repositories is an owner action**
— the shelf repos are outside this repository and were treated as
read-only during M0. Until then this directory is the canonical home of
the candidates (they must not live only in a session handoff). To apply:

1. Copy the candidate to the shelf root as `shelf.yml`
   (drop the `<shelf>.` prefix).
2. Run `openshelf validate --ci .` in the shelf root — expect exit 0.
3. Commit; optionally add the advisory CI stage from
   [`../advisory-ci.md`](../advisory-ci.md) in the same change.

Expected non-blocking findings on today's clones (exit code stays 0):
sqst-memshelf — none; unevie-shelf — `remote-mismatch` warning,
`no-policy` info; homelab-shelf — `remote-mismatch` and one `stale-index`
warning, `no-policy` info.

Once the candidate is merged as `shelf.yml`, delete it from this
directory — the shelf's own copy becomes the source of truth.
