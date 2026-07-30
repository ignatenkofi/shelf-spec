# Changelog

## Unreleased (M0)

- Pinned the MCP SDK by major (`mcp>=1.2.0,<2`): mcp 2.0.0 removed
  `mcp.server.fastmcp`, so fresh installs failed to import the server.
- **Project renamed `openshelf` → `shelf-spec`** (2026-07-26, ADR 0007;
  closes the naming gate #3): package, console script, module
  `shelf_spec`, env `SHELF_SPEC_ROOT` (was `OPENSHELF_ROOT`), schema `$id`,
  repo URLs. Nothing had been published under the old name.
- shelf-spec v0: `spec/SPEC.md` + `spec/shelf.schema.json` + examples.
- Engine: manifest loader (schema validation, config-error gate),
  spec validator with severities, idempotent scaffolder, info summary.
- Thin MCP server (`shelf_init` / `shelf_validate` / `shelf_info`) and
  CLI (`shelf-spec init|validate|info|serve`) over the same engine.
- `shelf-spec validate --ci` with exit codes 0/1/2 for shelf-repo CI.
- MCP tools take flat keyword arguments (`{"shelf_path": ...}` in
  `tools/call`) instead of a single nested `params` model.
- `docs/adoption/`: ready-to-apply `shelf.yml` candidates for the three
  owner shelves (validated green via `--manifest`; committing them into
  the shelf repos is an owner action).
- Validator: a non-UTF-8 or unreadable `.meta.json` / `ledger.tsv` /
  `.docshelf.json` now degrades to a normal finding instead of aborting
  the CLI with a traceback (#6).
- Validator: `extra_dirs` entries now suppress `category-undeclared` /
  `orphaned-split-dir` for the declared sidecar directories, and a declared
  directory missing on disk raises the `extra-dir-missing` info finding (#7).
- Validator: new `episode-sections-missing` error enforces the required
  H2 sections per episode kind (SPEC 5.3) (#8).
