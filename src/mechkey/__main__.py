"""Entry point for ``python -m mechkey``."""

from __future__ import annotations

import sys

from mechkey.cli import main

if __name__ == "__main__":
    sys.exit(main())
