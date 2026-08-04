# Changelog

## Unreleased

- **Ported the server to MCP SDK 2.x.** `FastMCP` (`mcp.server.fastmcp`)
  became `MCPServer` (`mcp.server.mcpserver`) in 2.0.0. The pin moves to
  `mcp>=2.0.0,<3` — a **floor**, not a raised ceiling: a 1.x install now
  fails at import. Done alongside `docshelf-mcp`, `memshelf-mcp` and
  `pii-mcp`, so every MCP server in the portfolio sits on one major.

  Two renames came with it, both caught by the existing tests: `call_tool`
  returns a `CallToolResult` instead of content blocks, and `Tool.inputSchema`
  is now `Tool.input_schema`.

- **`tests/test_stdio_protocol.py` — a real client over the real transport.**
  `test_server.py` drives tools through `mcp.call_tool` in-process, which
  covers validation and the JSON reply but never starts a server: no
  transport, no `serve` subcommand, no serialization.

  Measured, not assumed: breaking `_cmd_serve` so the entry point starts
  nothing leaves **83 in-process tests green** and fails only the three wire
  tests. The flat-argument contract (named arguments, not a nested `params`
  object) is now asserted on the far side of the transport too, since that is
  where a client actually reads it.

  `validate` is asserted as a pair — a real shelf comes back `valid` and a
  bare directory does not — because a validator that approved everything
  would satisfy the happy path alone.

## 0.1.0 (M0)

- Pinned the MCP SDK by major (`mcp>=1.2.0,<2`): mcp 2.0.0 removed
  `mcp.server.fastmcp`, so fresh installs failed to import the server.
  (Superseded above: the port landed and the pin moved to `>=2.0.0,<3`.)
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
