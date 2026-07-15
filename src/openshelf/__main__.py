"""``python -m openshelf`` — same as the ``openshelf`` console script."""

import sys

from openshelf.cli import main

sys.exit(main())
