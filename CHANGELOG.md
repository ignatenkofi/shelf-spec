# Changelog

## Unreleased (M0)

- shelf-spec v0: `spec/SPEC.md` + `spec/shelf.schema.json` + examples.
- Engine: manifest loader (schema validation, config-error gate),
  spec validator with severities, idempotent scaffolder, info summary.
- Thin MCP server (`shelf_init` / `shelf_validate` / `shelf_info`) and
  CLI (`openshelf init|validate|info|serve`) over the same engine.
- `openshelf validate --ci` with exit codes 0/1/2 for shelf-repo CI.
