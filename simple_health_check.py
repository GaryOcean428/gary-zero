#!/usr/bin/env python3
"""
Minimal health check server for Railway deployment fallback.
This ensures the deployment has a working health endpoint even if main.py fails.
"""

import os
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Gary-Zero Health Check")

@app.get("/health")
@app.get("/healthz")
@app.get("/ready")
async def health_check():
    """Simple health check endpoint for Railway."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": time.time(),
            "service": "gary-zero",
            "version": "1.0.0",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "local"),
            "message": "Minimal health check active"
        }
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Gary-Zero Health Check Active", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("WEB_UI_HOST", "0.0.0.0")
    print(f"🚀 Starting minimal health check server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)