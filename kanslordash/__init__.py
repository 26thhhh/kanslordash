"""KanslorDash: read-only fleet and network health dashboard."""

__version__ = "1.0.0"
__build_commit__ = ""


def get_version_string() -> str:
    if __build_commit__:
        return f"{__version__} ({__build_commit__})"
    return __version__

