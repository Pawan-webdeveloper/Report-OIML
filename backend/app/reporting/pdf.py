"""
WeasyPrint HTML → PDF. Lazy import: WeasyPrint needs GTK on Windows, so it is
an OPTIONAL dependency (install in Docker/WSL). Returns None when unavailable
— the API then answers 503 and the client falls back to browser print.
"""
from __future__ import annotations


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
        return True
    except Exception:          # ImportError or OSError (missing GTK libs)
        return False


def render_pdf(html: str) -> bytes | None:
    try:
        from weasyprint import HTML
    except Exception:
        return None
    return HTML(string=html).write_pdf()