#!/usr/bin/env python3
"""PyInstaller entry point for KANSLORDASH Windows executable."""

import sys

from kanslordash.cli import main

if __name__ == "__main__":
    sys.exit(main())

# Inject build metadata for packaged executable
try:
    import subprocess
    import sys
    from pathlib import Path
    # Try to read build info from file if present
    try:
        import kanslordash
        if hasattr(sys, '_MEIPASS'):
            build_info = Path(sys._MEIPASS) / 'BUILD_INFO'
            if build_info.exists():
                kanslordash.__build_commit__ = build_info.read_text().strip()
    except Exception:
        pass
except Exception:
    pass
