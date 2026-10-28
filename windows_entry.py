#!/usr/bin/env python3
"""PyInstaller entry point for KANSLORDASH Windows executable."""

import sys

from kanslordash.cli import main

if __name__ == "__main__":
    sys.exit(main())
