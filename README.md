# openshelf

**shelf-spec** — a portable, vendor-neutral memory format for AI agents —
plus a thin validator/scaffolder around it.

A *shelf* is a git repository of human-readable Markdown: categories, an
`INDEX.md` catalog, per-category metadata, an optional journal
(`ledger.tsv`) and policy (`POLICY.md`). Any MCP client attaches the same
shelf; migration between vendors is `git clone`. The product is the
**format** ([spec/SPEC.md](spec/SPEC.md)); the reference implementation is
[docshelf-mcp](https://github.com/ignatenkofi/docshelf-mcp).

Status: **v0 (draft, descriptive)** — the spec fixes what already works on
live shelves. The working name `openshelf` is not final (owner gate before
the production repo).

## What is in this repo

- `spec/SPEC.md` — shelf-spec v0 (RFC 2119).
- `spec/shelf.schema.json` — JSON Schema (draft 2020-12) for `shelf.yml`.
- `spec/examples/` — example manifests (memory, document, reserved multi).
- `src/openshelf/` — engine (manifest loader, validator, scaffolder, info)
  with two thin transports: an MCP server and a CLI.
- `docs/advisory-ci.md` — drop-in advisory CI stage for shelf repos.

## Install

```bash
pip install -e '.[dev]'
```

## CLI

```bash
openshelf init PATH --name "My shelf" --profile memory --categories topics,research,sessions
openshelf validate [PATH]              # human-readable report
openshelf validate --ci [PATH]         # machine JSON on stdout, exit 0/1/2
openshelf validate --json [PATH]       # JSON report
openshelf validate --manifest CANDIDATE.yml PATH   # validate a tree against
                                       # an external manifest without touching it
openshelf info [PATH]                  # manifest + index summary for a client
openshelf serve                        # MCP server on stdio
```

Exit codes: `0` — shelf conforms (warnings allowed; `--strict` promotes
warnings to failure), `1` — spec violations (error findings), `2` —
config-error (manifest missing / unparseable / schema-invalid; checked
before any rule).

The default shelf root is `$OPENSHELF_ROOT`, falling back to the current
directory.

## MCP server

Three tools, same engine as the CLI:

| tool | type | what it does |
|---|---|---|
| `shelf_init` | write (local) | scaffold a shelf: `shelf.yml`, docs root and categories, `POLICY.md` stub, `.gitignore`; idempotent |
| `shelf_validate` | read | lint a shelf against the spec; report with findings and severities |
| `shelf_info` | read | manifest + index summary for a connecting client |

Client configuration (stdio):

```json
{
  "mcpServers": {
    "openshelf": {
      "command": "openshelf",
      "args": ["serve"],
      "env": { "OPENSHELF_ROOT": "/path/to/your/shelf" }
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
`shelf.yml` is the contract.

## License

MIT.
