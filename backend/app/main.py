from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import REPO_ROOT
from app.db import init_db
from app.routers import annotate, auth, cars, meta, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Project X API",
    description="Detects car damage in an uploaded image, estimates severity, "
    "and returns a repair cost quotation.",
    version="0.1.0",
    lifespan=lifespan,
)

# Wide-open CORS for local development (React dev server on a different
# port). Tighten this to specific origins before deploying anywhere shared.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(annotate.router)
app.include_router(auth.router)
app.include_router(cars.router)
app.include_router(meta.router)
app.include_router(reports.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Optional single-service deployment: if the frontend has been built
# (`npm run build` in frontend/, producing frontend/dist), serve it
# directly from the same FastAPI process instead of running a separate
# frontend host. Mounted last so it never shadows the /api/* routes
# above — Starlette tries routes in registration order, and this "/"
# mount only catches what nothing else matched. Local dev (npm run dev)
# doesn't need this at all; it's for a single deployed URL.
_frontend_dist = REPO_ROOT / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
