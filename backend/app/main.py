from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
