"""
WeasyPrint HTML → PDF. Lazy import: WeasyPrint needs GTK on Windows, so it is
an OPTIONAL dependency (install in Docker/WSL). Returns None when unavailable
— the API then answers 503 and the client falls back to browser print.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _configure_native_libraries() -> None:
    """Let macOS Python processes find Homebrew's Pango/GLib libraries."""
    if sys.platform != "darwin":
        return
    homebrew_lib = Path("/opt/homebrew/lib")
    if homebrew_lib.is_dir():
        current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        paths = [p for p in current.split(":") if p]
        if str(homebrew_lib) not in paths:
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(
                [str(homebrew_lib), *paths]
            )


def weasyprint_available() -> bool:
    _configure_native_libraries()
    try:
        import weasyprint  # noqa: F401
        return True
    except Exception:          # ImportError or OSError (missing GTK libs)
        return False


def render_pdf(html: str) -> bytes | None:
    _configure_native_libraries()
    try:
        from weasyprint import HTML
    except Exception:
        return None
    return HTML(string=html).write_pdf()
