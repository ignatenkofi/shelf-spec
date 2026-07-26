"""``shelf-spec`` CLI — the same engine as the MCP server, second transport.

Commands: ``init``, ``validate``, ``info``, ``serve``. Exit-code contract
(SPEC.md 9.2, shared with the house verify tools): 0 = conforms (warnings
allowed), 1 = error findings, 2 = config-error (manifest missing /
unparseable / schema-invalid — checked before any rule).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shelf_spec import __version__
from shelf_spec.config import default_shelf_root
from shelf_spec.engine import ManifestError, init_shelf, shelf_info, validate_shelf

__all__ = ["main"]

EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_CONFIG_ERROR = 2


def _resolve_root(path: str | None) -> Path:
    return Path(path).expanduser().resolve() if path else default_shelf_root()


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _cmd_init(args: argparse.Namespace) -> int:
    categories = [c.strip() for c in (args.categories or "").split(",") if c.strip()]
    try:
        payload = init_shelf(
            _resolve_root(args.path),
            name=args.name,
            mode=args.mode,
            profile=args.profile,
            categories=categories,
        )
    except ManifestError as exc:
        # An existing shelf.yml that fails the schema gate: refuse rather than
        # scaffold onto a broken contract (same exit code as validate/info).
        print(f"config-error ({exc.rule}): {exc.detail}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if args.json:
        _print_json(payload)
    else:
        print(f"shelf: {payload['shelf_root']}")
        for item in payload["created"]:
            print(f"  created  {item}")
        for item in payload["skipped"]:
            print(f"  skipped  {item} (already exists)")
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    report = validate_shelf(_resolve_root(args.path), args.manifest)
    if args.ci or args.json:
        _print_json(report)
    else:
        print(f"shelf:   {report['shelf_root']}")
        print(f"verdict: {report['verdict']} ({report['finding_count']} finding(s))")
        for f in report["findings"]:
            print(f"  [{f['severity']}] {f['rule']} — {f['path']}")
            print(f"      {f['detail']}")
            print(f"      fix: {f['suggested_fix']}")

    if report["verdict"] == "config-error":
        return EXIT_CONFIG_ERROR
    if report["verdict"] == "violations":
        return EXIT_VIOLATIONS
    if args.strict and any(f["severity"] == "warning" for f in report["findings"]):
        return EXIT_VIOLATIONS
    return EXIT_OK


def _cmd_info(args: argparse.Namespace) -> int:
    try:
        payload = shelf_info(_resolve_root(args.path))
    except ManifestError as exc:
        print(f"config-error ({exc.rule}): {exc.detail}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    if args.json:
        _print_json(payload)
    else:
        print(f"name:         {payload['name'] or '(unnamed)'}")
        print(f"shelf:        {payload['shelf_root']}")
        print(f"spec_version: {payload['spec_version']}   mode: {payload['mode']}   "
              f"profile: {payload['profile']}")
        print(f"docs_root:    {payload['docs_root']}")
        print("categories:")
        for cat in payload["categories"]:
            print(f"  {cat['name']}: {cat['documents']} document(s), "
                  f"{cat['split_documents']} split")
        print(f"index:        generated_by={payload['index_generated_by']} "
              f"present={payload['has_index']}")
        print(f"ledger:       {payload['has_ledger']}   policy: {payload['has_policy']}")
        reserved = payload["reserved"]
        if reserved["agents"] or reserved["provenance"]:
            print(f"reserved M1:  agents={reserved['agents']} "
                  f"provenance={reserved['provenance']}")
        if payload["index_preamble"]:
            print("preamble:")
            for line in payload["index_preamble"].splitlines():
                print(f"  {line}")
    return EXIT_OK


def _cmd_serve(_args: argparse.Namespace) -> int:
    from shelf_spec.server import main as server_main

    server_main([])
    return EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shelf-spec",
        description="shelf-spec tooling: scaffold, validate, and summarize shelves.",
    )
    parser.add_argument("--version", action="version", version=f"shelf-spec {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold a spec-conformant shelf (idempotent)")
    p_init.add_argument("path", nargs="?", default=None, help="shelf root (default: $SHELF_SPEC_ROOT or cwd)")
    p_init.add_argument("--name", default="", help="human-readable shelf name")
    p_init.add_argument("--mode", choices=["single", "multi"], default="single")
    p_init.add_argument("--profile", choices=["memory", "document"], default="document")
    p_init.add_argument("--categories", default="", help="comma-separated category list")
    p_init.add_argument("--json", action="store_true", help="machine-readable output")
    p_init.set_defaults(func=_cmd_init)

    p_val = sub.add_parser("validate", help="lint a shelf against shelf-spec (exit 0/1/2)")
    p_val.add_argument("path", nargs="?", default=None, help="shelf root (default: $SHELF_SPEC_ROOT or cwd)")
    p_val.add_argument(
        "--manifest",
        default=None,
        metavar="PATH",
        help="external shelf.yml candidate — validate the tree against it "
        "without requiring or touching a manifest inside the shelf",
    )
    p_val.add_argument("--ci", action="store_true", help="machine JSON output for CI")
    p_val.add_argument("--json", action="store_true", help="JSON report")
    p_val.add_argument("--strict", action="store_true", help="warnings also fail (exit 1)")
    p_val.set_defaults(func=_cmd_validate)

    p_info = sub.add_parser("info", help="manifest + index summary for a client")
    p_info.add_argument("path", nargs="?", default=None, help="shelf root (default: $SHELF_SPEC_ROOT or cwd)")
    p_info.add_argument("--json", action="store_true", help="machine-readable output")
    p_info.set_defaults(func=_cmd_info)

    p_serve = sub.add_parser("serve", help="run the MCP server on stdio")
    p_serve.set_defaults(func=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
