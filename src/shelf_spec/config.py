"""Server/CLI-level configuration (env vars).

``SHELF_SPEC_ROOT`` is the default shelf directory used when a tool or CLI
command is invoked without an explicit path. If unset, the current working
directory is used — the right behaviour when running from inside a shelf.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["default_shelf_root"]


def default_shelf_root() -> Path:
    """Resolve the default shelf root for calls without an explicit path."""
    env = os.environ.get("SHELF_SPEC_ROOT", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()
