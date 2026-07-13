#!/usr/bin/env python3
"""SICA -- self-improving coding agent engine. Thin entrypoint.

Usage:
    python3 sica.py pin            [--profile smoke]
    python3 sica.py validate-bench [--profile smoke] [--fixtures]
    python3 sica.py estimate       [--profile smoke]
    python3 sica.py verify         [--seed v1]          # $0 stub end-to-end
    python3 sica.py run --profile smoke --backend claude_cli --yes --max-cost 12
    python3 sica.py report         [--profile smoke] [--seed s1]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runner.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
