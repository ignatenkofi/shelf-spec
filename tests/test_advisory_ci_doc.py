"""docs/advisory-ci.md installs the release this checkout is (shelf-spec#62).

Shelf repositories copy the page's job as is, so a stale pin there is a
stale validator in each of them: 0.3.0 shipped while the page still said
``>=0.2,<0.3``, which installs 0.2.x, without the rules 0.3.0 added. The
pins are read from the page itself, so a release that bumps
``__version__`` without the page goes red here, whatever the version is.
"""

from __future__ import annotations

import re

from packaging.specifiers import SpecifierSet  # a hard dependency of pytest
from packaging.version import Version

from shelf_spec import __version__
from tests.conftest import REPO_ROOT

DOC = REPO_ROOT / "docs" / "advisory-ci.md"

_PINNED_INSTALL = re.compile(r'pip install "shelf-spec([^"]*)"')


def test_doc_pins_admit_the_current_version_and_stop_at_the_next_minor() -> None:
    pins = _PINNED_INSTALL.findall(DOC.read_text(encoding="utf-8"))
    # The job and the "Published release" route; the git+ route is unpinned.
    assert len(pins) == 2, pins
    current = Version(__version__)
    next_minor = Version(f"{current.major}.{current.minor + 1}")
    for spec in pins:
        assert current in SpecifierSet(spec), f"shelf-spec{spec} does not install {current}"
        # "Pin by minor", as the page says: an open range would pass the
        # check above and still pull in rules nobody reviewed.
        assert next_minor not in SpecifierSet(spec), f"shelf-spec{spec} is not pinned by minor"
