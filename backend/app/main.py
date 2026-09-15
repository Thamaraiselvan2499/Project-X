from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import annotate

app = FastAPI(
    title="Project X API",
    description="Detects car damage in an uploaded image, estimates severity, "
    "and returns a repair cost quotation.",
    version="0.1.0",
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


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
