# shelf-spec

**shelf-spec** — a portable, vendor-neutral memory format for AI agents —
plus a thin validator/scaffolder around it.

A *shelf* is a git repository of human-readable Markdown: categories, an
`INDEX.md` catalog, per-category metadata, an optional journal
(`ledger.tsv`) and policy (`POLICY.md`). Any MCP client attaches the same
shelf; migration between vendors is `git clone`. The product is the
**format** ([spec/SPEC.md](spec/SPEC.md)); the reference implementation is
[docshelf-mcp](https://github.com/ignatenkofi/docshelf-mcp).

Status: **v0 (draft, descriptive)** — the spec fixes what already works on
live shelves. Final name: `shelf-spec` (decided 2026-07-26, ADR 0007; before
the production repo).

## What is in this repo

- `spec/SPEC.md` — shelf-spec v0 (RFC 2119).
- `spec/shelf.schema.json` — JSON Schema (draft 2020-12) for `shelf.yml`.
- `spec/examples/` — example manifests (memory, document, reserved multi).
- `src/shelf_spec/` — engine (manifest loader, validator, scaffolder, info)
  with two thin transports: an MCP server and a CLI.
- `docs/advisory-ci.md` — drop-in advisory CI stage for shelf repos.

## Install

```bash
pip install -e '.[dev]'
```

## CLI

```bash
shelf-spec init PATH --name "My shelf" --profile memory --categories topics,research,sessions
shelf-spec validate [PATH]              # human-readable report
shelf-spec validate --ci [PATH]         # machine JSON on stdout, exit 0/1/2
shelf-spec validate --json [PATH]       # JSON report
shelf-spec validate --manifest CANDIDATE.yml PATH   # validate a tree against
                                       # an external manifest without touching it
shelf-spec info [PATH]                  # manifest + index summary for a client
shelf-spec serve                        # MCP server on stdio
```

Exit codes: `0` — shelf conforms (warnings allowed; `--strict` promotes
warnings to failure), `1` — spec violations (error findings), `2` —
config-error (manifest missing / unparseable / schema-invalid; checked
before any rule).

The default shelf root is `$SHELF_SPEC_ROOT`, falling back to the current
directory.

## MCP server

Three tools, same engine as the CLI:

| tool | type | what it does |
|---|---|---|
| `shelf_init` | write (local) | scaffold a shelf: `shelf.yml`, docs root and categories, `POLICY.md` stub, `.gitignore`; idempotent |
| `shelf_validate` | read | lint a shelf against the spec; report with findings and severities |
| `shelf_info` | read | manifest + index summary for a connecting client |

Tools take flat keyword arguments — a hand-written `tools/call` looks like
`{"name": "shelf_validate", "arguments": {"shelf_path": "/path/to/shelf"}}`,
no wrapper object.

Client configuration (stdio):

```json
{
  "mcpServers": {
    "shelf-spec": {
      "command": "shelf-spec",
      "args": ["serve"],
      "env": { "SHELF_SPEC_ROOT": "/path/to/your/shelf" }
    }
  }
}
```

Validation and info never scaffold a shelf silently: pointing them at a
directory without a manifest is a config-error, not an invitation to
create one.

## Compatibility promise

An existing docshelf/memshelf shelf becomes spec-conformant by adding
**one file** — `shelf.yml` with `mode: single`. Nothing is migrated
(ADR-0005). `.docshelf.json` remains a legal implementation detail;
`shelf.yml` is the contract. Ready-to-apply manifests for the shelves
named in the roadmap live in [`docs/adoption/`](docs/adoption/README.md).

## License

MIT.
