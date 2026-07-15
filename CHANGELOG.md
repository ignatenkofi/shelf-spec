# Changelog

## Unreleased (M0)

- shelf-spec v0: `spec/SPEC.md` + `spec/shelf.schema.json` + examples.
- Engine: manifest loader (schema validation, config-error gate),
  spec validator with severities, idempotent scaffolder, info summary.
- Thin MCP server (`shelf_init` / `shelf_validate` / `shelf_info`) and
  CLI (`openshelf init|validate|info|serve`) over the same engine.
- `openshelf validate --ci` with exit codes 0/1/2 for shelf-repo CI.
- MCP tools take flat keyword arguments (`{"shelf_path": ...}` in
  `tools/call`) instead of a single nested `params` model.
- `docs/adoption/`: ready-to-apply `shelf.yml` candidates for the three
  owner shelves (validated green via `--manifest`; committing them into
  the shelf repos is an owner action).
