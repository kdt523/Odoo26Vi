"""
app/main.py — FastAPI application entry point for core-api.

Registers all 7 routers under /api prefix.
CORS is wide-open for development — restrict in production.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, org, assets, allocations, bookings, maintenance, audits, dashboard, reports

# ── Application factory ────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AssetFlow Core API — asset registry, allocation, booking, maintenance & audit. "
        "This is the scaffold pass: all endpoints return 501 until implemented."
    ),
    version="0.1.0-scaffold",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: restrict to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
API_PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router,        prefix=API_PREFIX)
app.include_router(org.router,         prefix=API_PREFIX)
app.include_router(assets.router,      prefix=API_PREFIX)
app.include_router(allocations.router, prefix=API_PREFIX)
app.include_router(bookings.router,    prefix=API_PREFIX)
app.include_router(maintenance.router, prefix=API_PREFIX)
app.include_router(audits.router,      prefix=API_PREFIX)
app.include_router(dashboard.router,   prefix=API_PREFIX)
app.include_router(reports.router,     prefix=API_PREFIX)


# ── Health check ───────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "core-api"}


# ── Startup / shutdown events ──────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    # TODO: verify DB connectivity, warm caches if needed
    pass


@app.on_event("shutdown")
async def on_shutdown():
    # TODO: clean up connections
    pass
