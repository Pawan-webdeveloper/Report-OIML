from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import calc

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server (Phase 6)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calc.router, prefix=settings.API_PREFIX)


@app.get(settings.API_PREFIX + "/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}

# More routers will be included here from Phase 5 onwards:
# app.include_router(instruments.router, prefix=settings.API_PREFIX)