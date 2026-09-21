# Adoption kit — shelf.yml candidates for the owner's shelves

Ready-to-apply `shelf.yml` manifests for the three existing shelves named
in the M0 roadmap. Each one makes its shelf spec-conformant by adding a
single file (`mode: single`, compatibility promise of ADR-0005) — nothing
else migrates.

| candidate | target shelf | profile | notes |
|---|---|---|---|
| *(applied, removed)* | main-memshelf (then `sqst-memshelf`) | memory | ledger + policy declared; `shelf.yml` lives in the shelf since 2026-08-21 |
| `unevie-shelf.shelf.yml` | unevie-shelf | document | older `.docshelf.json` stays valid |
| *(applied, removed)* | homelab-iac/hardware-shelf (then `homelab-shelf`) | document | pre-docshelf: nested docs root, external index, extra dirs; `shelf.yml` lives in the shelf — in `homelab-iac` since 2026-09-14 (homelab-iac#155), validated there by `shelf-validate.yml` without `--manifest` |

A candidate validates green (`exit 0`, zero error findings) against the live
clone via the external-manifest mode, which needs no write access to the
shelf:

```bash
shelf-spec validate --ci --manifest docs/adoption/<shelf>.shelf.yml /path/to/<shelf>
```

## Status: one candidate still waiting

> **2026-09-05.** `main-memshelf` (renamed from `sqst-memshelf` in August)
> has carried its own `shelf.yml` since 2026-08-21, so its candidate was
> removed from this directory as the rule at the end of this page requires.
> The two rows below are the candidates still waiting.
>
> **2026-09-21.** `homelab-shelf` carried its candidate as `shelf.yml` and
> moved into `homelab-iac` as the `hardware-shelf/` directory on 2026-09-14
> (homelab-iac#155); the manifest is identical to the candidate up to the
> header comment and is validated there by `shelf-validate.yml`. The
> candidate is removed; `unevie-shelf` is the one row still waiting.

Committing these files **into the shelf repositories is an owner action**
— the shelf repos are outside this repository and were treated as
read-only during M0. Until then this directory is the canonical home of
the candidates (they must not live only in a session handoff). To apply:

1. Copy the candidate to the shelf root as `shelf.yml`
   (drop the `<shelf>.` prefix).
2. Run `shelf-spec validate --ci .` in the shelf root — expect exit 0.
3. Commit; optionally add the advisory CI stage from
   [`../advisory-ci.md`](../advisory-ci.md) in the same change.

Expected non-blocking findings on the clones as measured at drafting time
(exit code stays 0): main-memshelf (measured as `sqst-memshelf`) — none;
unevie-shelf — `remote-mismatch` warning, `no-policy` info; homelab-shelf
(applied; now `homelab-iac/hardware-shelf`) — `remote-mismatch` and one
`stale-index` warning, `no-policy` info.

Once the candidate is merged as `shelf.yml`, delete it from this
directory — the shelf's own copy becomes the source of truth.
