from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.config import get_settings
from .routers import (attachments, audit, auth, calc, dashboard, equipment,
                      evaluations, instruments, parties, reports, rulesets,
                      tests, users)

settings = get_settings()
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"

app = FastAPI(
    title=settings.APP_NAME,
    version="0.5.0",
    docs_url="/docs",
)

_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(parties.router, prefix=settings.API_PREFIX)
app.include_router(instruments.router, prefix=settings.API_PREFIX)
app.include_router(equipment.router, prefix=settings.API_PREFIX)
app.include_router(evaluations.router, prefix=settings.API_PREFIX)
app.include_router(tests.router, prefix=settings.API_PREFIX)
app.include_router(attachments.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(rulesets.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(calc.router, prefix=settings.API_PREFIX)


@app.get(settings.API_PREFIX + "/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}


def _serve_spa(full_path: str = ""):
    """Serve the Vite build from backend/public; unknown paths → index.html."""
    index = PUBLIC_DIR / "index.html"
    if full_path:
        candidate = (PUBLIC_DIR / full_path).resolve()
        try:
            candidate.relative_to(PUBLIC_DIR.resolve())
        except ValueError:
            candidate = None
        if candidate is not None and candidate.is_file():
            return FileResponse(candidate)
    if index.is_file():
        return FileResponse(index)
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "api": settings.API_PREFIX,
        "frontend": "not built — run npm run build:backend in frontend/",
    }


if (PUBLIC_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=PUBLIC_DIR / "assets"), name="assets")

app.add_api_route("/", _serve_spa, methods=["GET"], include_in_schema=False)
app.add_api_route("/{full_path:path}", _serve_spa, methods=["GET"], include_in_schema=False)