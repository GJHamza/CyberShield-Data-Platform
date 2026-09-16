"""
CyberShield Data Platform - FastAPI Main Application
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api.config import (
    API_PREFIX,
    CORS_ORIGINS,
    DEBUG,
    PROJECT_NAME,
    PROJECT_VERSION,
)
from services.api.routes import alerts, events, health, statistics

app = FastAPI(
    title=PROJECT_NAME,
    version=PROJECT_VERSION,
    description="CyberShield Security Operations REST API for event exploration, ML alerts, and threat analytics.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(events.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(statistics.router, prefix=API_PREFIX)


@app.get("/", tags=["Root"])
def root():
    """API Root Welcome Endpoint."""
    return {
        "service": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_check": f"{API_PREFIX}/health",
    }


# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler ensuring sensitive information is never leaked."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please consult system logs."},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
