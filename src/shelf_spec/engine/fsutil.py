"""Small filesystem helpers (pattern: docshelf-mcp core/fsutil).

:func:`atomic_write_text` writes via a same-directory temp file and
``os.replace`` so an interrupted write never leaves a torn manifest,
policy, or ledger behind.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

__all__ = ["atomic_write_text"]


def atomic_write_text(path: Path | str, text: str, *, encoding: str = "utf-8") -> None:
    """Write ``text`` to ``path`` atomically (same-filesystem rename)."""
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    try:
        umask = os.umask(0)
        os.umask(umask)
        try:
            os.chmod(tmp_name, 0o666 & ~umask)
        except OSError:
            pass  # best-effort; not fatal
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
