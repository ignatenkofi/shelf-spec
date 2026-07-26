"""Engine — all shelf logic lives here; the MCP server and CLI stay thin.

The engine never touches the network and never mutates git state. The only
writing entry point is :mod:`shelf_spec.engine.initializer`; everything else
is read-only.
"""

from shelf_spec.engine.info import shelf_info
from shelf_spec.engine.initializer import init_shelf
from shelf_spec.engine.manifest import Manifest, ManifestError, load_manifest
from shelf_spec.engine.validator import Finding, validate_shelf

__all__ = [
    "Manifest",
    "ManifestError",
    "load_manifest",
    "Finding",
    "validate_shelf",
    "init_shelf",
    "shelf_info",
]
