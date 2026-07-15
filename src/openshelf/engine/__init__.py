"""Engine — all shelf logic lives here; the MCP server and CLI stay thin.

The engine never touches the network and never mutates git state. The only
writing entry point is :mod:`openshelf.engine.initializer`; everything else
is read-only.
"""

from openshelf.engine.info import shelf_info
from openshelf.engine.initializer import init_shelf
from openshelf.engine.manifest import Manifest, ManifestError, load_manifest
from openshelf.engine.validator import Finding, validate_shelf

__all__ = [
    "Manifest",
    "ManifestError",
    "load_manifest",
    "Finding",
    "validate_shelf",
    "init_shelf",
    "shelf_info",
]
