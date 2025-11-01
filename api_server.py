#!/usr/bin/env python3
"""
API server entry point for Address Cleanser.

Usage:
    python api_server.py
    uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.endpoints import router
from src.api.middleware import APIKeyMiddleware, RateLimitMiddleware

# Configure API keys from environment (optional)
API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "60"))  # requests per minute

# Create FastAPI app
app = FastAPI(
    title="Address Cleanser API",
    description=(
        "REST API for parsing, validating, and formatting US addresses "
        "according to USPS Publication 28 standards"
    ),
    version="1.0.12",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=RATE_LIMIT)

# Add API key middleware if keys are configured
if API_KEYS:
    app.add_middleware(APIKeyMiddleware, api_keys=API_KEYS)

# Include API router
app.include_router(router, prefix="/api/v1", tags=["address"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Address Cleanser API",
        "version": "1.0.12",
        "docs": "/docs",
        "health": "/api/v1/health",
        "authentication": (
            "X-API-Key header required" if API_KEYS else "No authentication required"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
