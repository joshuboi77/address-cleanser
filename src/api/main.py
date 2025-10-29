"""
FastAPI application for Address Cleanser API.

This module creates and configures the FastAPI app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import router

# Create FastAPI app
app = FastAPI(
    title="Address Cleanser API",
    description="REST API for parsing, validating, and formatting US addresses",
    version="1.0.0",
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

# Include API router
app.include_router(router, prefix="/api/v1", tags=["address"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Address Cleanser API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }

