"""Jinja2 HTML rendering of the report model (shared by preview + PDF)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_env: Environment | None = None


def _env_or_create() -> Environment:
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "templates"),
            autoescape=select_autoescape(["html"]),
        )
    return _env


def render_html(model: dict) -> str:
    return _env_or_create().get_template("report.html.j2").render(**model)