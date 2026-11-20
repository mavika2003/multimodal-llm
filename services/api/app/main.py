from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import demo, health, incidents, inspector, scans
from app.settings import settings

app = FastAPI(title="AIRLOCK API", version="0.1.0")

origins = settings.allowed_origin_prefixes()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in origins if o.startswith("http")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI()
api.include_router(health.router)
api.include_router(scans.router)
api.include_router(incidents.router)
api.include_router(inspector.router)
api.include_router(demo.router)

app.mount("/api/v1", api)


@app.get("/")
def root() -> dict:
    return {"name": "AIRLOCK", "api": "/api/v1/health"}