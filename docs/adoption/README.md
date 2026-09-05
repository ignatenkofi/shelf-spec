# Adoption kit — shelf.yml candidates for the owner's shelves

Ready-to-apply `shelf.yml` manifests for the three existing shelves named
in the M0 roadmap. Each one makes its shelf spec-conformant by adding a
single file (`mode: single`, compatibility promise of ADR-0005) — nothing
else migrates.

| candidate | target shelf | profile | notes |
|---|---|---|---|
| *(applied, removed)* | main-memshelf (then `sqst-memshelf`) | memory | ledger + policy declared; `shelf.yml` lives in the shelf since 2026-08-21 |
| `unevie-shelf.shelf.yml` | unevie-shelf | document | older `.docshelf.json` stays valid |
| `homelab-shelf.shelf.yml` | homelab-shelf | document | pre-docshelf: nested docs root, external index, extra dirs |

All three validate green (`exit 0`, zero error findings) against the live
clones via the external-manifest mode, which needs no write access to the
shelf:

```bash
shelf-spec validate --ci --manifest docs/adoption/<shelf>.shelf.yml /path/to/<shelf>
```

## Status: drafted, not yet applied

> **2026-09-05.** `main-memshelf` (renamed from `sqst-memshelf` in August)
> has carried its own `shelf.yml` since 2026-08-21, so its candidate was
> removed from this directory as the rule at the end of this page requires.
> The two rows below are the candidates still waiting.

Committing these files **into the shelf repositories is an owner action**
— the shelf repos are outside this repository and were treated as
read-only during M0. Until then this directory is the canonical home of
the candidates (they must not live only in a session handoff). To apply:

1. Copy the candidate to the shelf root as `shelf.yml`
   (drop the `<shelf>.` prefix).
2. Run `shelf-spec validate --ci .` in the shelf root — expect exit 0.
3. Commit; optionally add the advisory CI stage from
   [`../advisory-ci.md`](../advisory-ci.md) in the same change.

Expected non-blocking findings on today's clones (exit code stays 0):
main-memshelf (measured as `sqst-memshelf`) — none; unevie-shelf — `remote-mismatch` warning,
`no-policy` info; homelab-shelf — `remote-mismatch` and one `stale-index`
warning, `no-policy` info.

Once the candidate is merged as `shelf.yml`, delete it from this
directory — the shelf's own copy becomes the source of truth.
