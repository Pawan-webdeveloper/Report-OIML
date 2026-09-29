from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import (attachments, audit, auth, calc, dashboard, equipment,
                      evaluations, instruments, parties, reports, rulesets,
                      tests, users)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.5.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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