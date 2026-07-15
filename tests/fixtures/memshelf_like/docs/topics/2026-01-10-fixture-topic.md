# 2026-01-10-fixture-topic

---
id: 2026-01-10-fixture-topic
kind: topic
span: 2026-01-10
tags: [fixture, openshelf]
approx_tokens: 1500
mode: live
---

## Digest

Synthetic topic episode. Decided to use flat fixtures for the openshelf
test suite; rejected generating fixtures at test time because on-disk
fixtures document the format for humans too. Artifacts: this file, the
category .meta.json, one ledger row. Open: nothing.

## Decisions

- **Flat on-disk fixtures** — readable documentation of the format;
  rejected: runtime generation (opaque, drifts from the spec).
