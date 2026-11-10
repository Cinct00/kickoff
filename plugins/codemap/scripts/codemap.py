#!/usr/bin/env python3
"""codemap — token-efficient repository map. Run `codemap.py --help`."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codemap_core.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
