"""
WonderPy AI-Interface Backend
FastAPI Application Entry Point
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any

from api.routes import robot, sensors, ai, voice, plugins, websocket
from api.middleware.error_handler import add_exception_handlers
from utils.config import settings
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    logger.info("🚀 Starting WonderPy AI-Interface Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    # TODO: Initialize services
    # - Database connection
    # - Redis connection
    # - Plugin system
    # - Robot manager

    yield

    logger.info("🛑 Shutting down WonderPy AI-Interface Backend...")

    # TODO: Cleanup
    # - Close database connections
    # - Disconnect robots
    # - Cleanup plugins


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Enhanced Full-Stack Control System for WonderWorkshop Dash Robots",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(robot.router, prefix="/api/v1/robots", tags=["Robot Control"])
app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["Sensors"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Agent"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["Plugins"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {
        "message": "WonderPy AI-Interface API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/info")
async def info() -> Dict[str, Any]:
    """System information endpoint"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
