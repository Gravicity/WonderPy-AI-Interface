# FastAPI Backend Best Practices for Robotics Control Systems

## Executive Summary

This document provides comprehensive architectural recommendations and code patterns for building production-ready FastAPI backends for robotics control systems. Based on current industry best practices (2025), this guide covers structure, API design, real-time communication, background processing, error handling, security, rate limiting, and async patterns specifically tailored for hardware control applications.

---

## Table of Contents

1. [Application Structure for Hardware Control](#1-application-structure-for-hardware-control)
2. [REST API Design Patterns for Robot Commands](#2-rest-api-design-patterns-for-robot-commands)
3. [WebSocket Integration for Real-Time Sensor Streaming](#3-websocket-integration-for-real-time-sensor-streaming)
4. [Background Task Management for Sensor Polling](#4-background-task-management-for-sensor-polling)
5. [Error Handling and Safety Mechanisms](#5-error-handling-and-safety-mechanisms)
6. [Authentication and Security](#6-authentication-and-security)
7. [Rate Limiting and Request Queuing](#7-rate-limiting-and-request-queuing)
8. [Async Patterns for Non-Blocking Hardware Operations](#8-async-patterns-for-non-blocking-hardware-operations)
9. [Complete Reference Architecture](#9-complete-reference-architecture)

---

## 1. Application Structure for Hardware Control

### Recommended Layered Architecture

Use a **service-layer architecture** with clear separation of concerns:

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app initialization
│   ├── config.py                    # Configuration management
│   ├── dependencies.py              # Dependency injection setup
│   │
│   ├── api/                         # API/Controller Layer
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── robot.py         # Robot control endpoints
│   │   │   │   ├── sensors.py       # Sensor endpoints
│   │   │   │   ├── configuration.py # Configuration endpoints
│   │   │   │   └── websocket.py     # WebSocket endpoints
│   │   │   └── router.py            # API router aggregation
│   │   │
│   ├── services/                    # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── robot_service.py         # Robot control logic
│   │   ├── sensor_service.py        # Sensor management logic
│   │   └── safety_service.py        # Safety checks and validations
│   │
│   ├── hardware/                    # Hardware Abstraction Layer
│   │   ├── __init__.py
│   │   ├── robot_interface.py       # Abstract robot interface
│   │   ├── dash_robot.py            # Concrete implementation (Dash)
│   │   ├── sensor_manager.py        # Sensor polling and management
│   │   └── connection_manager.py    # Hardware connection management
│   │
│   ├── models/                      # Pydantic Models
│   │   ├── __init__.py
│   │   ├── requests.py              # Request models
│   │   ├── responses.py             # Response models
│   │   └── sensor_data.py           # Sensor data models
│   │
│   ├── core/                        # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── security.py              # Security utilities
│   │   └── websocket_manager.py     # WebSocket connection manager
│   │
│   └── middleware/                  # Middleware
│       ├── __init__.py
│       ├── error_handler.py         # Global error handling
│       ├── rate_limiter.py          # Rate limiting middleware
│       └── logging.py               # Request/response logging
│
├── tests/
├── requirements.txt
└── docker-compose.yml
```

### Main Application Setup

**`app/main.py`**:
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.api.v1.router import api_router
from app.core.exceptions import RobotException, SafetyException
from app.hardware.connection_manager import ConnectionManager
from app.config import settings

logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    logger.info("Starting robot control system...")
    app.state.connection_manager = ConnectionManager()
    await app.state.connection_manager.initialize()

    yield

    # Shutdown
    logger.info("Shutting down robot control system...")
    await app.state.connection_manager.cleanup()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Robot Control API",
    description="FastAPI backend for robotics control",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Global exception handlers
@app.exception_handler(RobotException)
async def robot_exception_handler(request: Request, exc: RobotException):
    """Handle robot-specific exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_type,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(SafetyException)
async def safety_exception_handler(request: Request, exc: SafetyException):
    """Handle safety-critical exceptions with immediate robot halt."""
    logger.critical(f"Safety exception: {exc.message}")
    # Emergency stop
    if hasattr(app.state, 'connection_manager'):
        await app.state.connection_manager.emergency_stop()

    return JSONResponse(
        status_code=503,
        content={
            "error": "SAFETY_VIOLATION",
            "message": exc.message,
            "action_taken": "EMERGENCY_STOP"
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "robot_connected": app.state.connection_manager.is_connected()
    }
```

### Configuration Management

**`app/config.py`**:
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Robot Control API"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Robot Hardware
    ROBOT_CONNECTION_TIMEOUT: int = 30
    SENSOR_POLL_INTERVAL: float = 0.1  # 100ms
    MAX_COMMAND_QUEUE_SIZE: int = 100

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_SECOND: int = 10

    # Safety
    ENABLE_SAFETY_CHECKS: bool = True
    MAX_VELOCITY: float = 1.0  # meters/second
    MIN_OBSTACLE_DISTANCE: float = 0.2  # meters

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Dependency Injection Pattern

**`app/dependencies.py`**:
```python
from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.hardware.robot_interface import RobotInterface
from app.services.robot_service import RobotService
from app.services.sensor_service import SensorService
from app.services.safety_service import SafetyService
from app.core.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate JWT token and return user info."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await verify_token(token)
    if user is None:
        raise credentials_exception
    return user

def get_robot_interface(request: Request) -> RobotInterface:
    """Get robot hardware interface from app state."""
    if not hasattr(request.app.state, 'connection_manager'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Robot interface not initialized"
        )
    return request.app.state.connection_manager.get_robot()

def get_robot_service(
    robot: RobotInterface = Depends(get_robot_interface)
) -> RobotService:
    """Create robot service instance."""
    return RobotService(robot)

def get_sensor_service(
    robot: RobotInterface = Depends(get_robot_interface)
) -> SensorService:
    """Create sensor service instance."""
    return SensorService(robot)

def get_safety_service() -> SafetyService:
    """Create safety service instance."""
    return SafetyService()
```

---

## 2. REST API Design Patterns for Robot Commands

### Command Endpoint Structure

**`app/api/v1/endpoints/robot.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional
import asyncio

from app.models.requests import (
    MoveCommand, RotateCommand, HeadCommand,
    LEDCommand, SoundCommand
)
from app.models.responses import CommandResponse, RobotStatus
from app.services.robot_service import RobotService
from app.services.safety_service import SafetyService
from app.dependencies import (
    get_robot_service, get_safety_service, get_current_user
)

router = APIRouter(prefix="/robot", tags=["robot"])

@router.get("/status", response_model=RobotStatus)
async def get_robot_status(
    robot_service: RobotService = Depends(get_robot_service),
    current_user: dict = Depends(get_current_user)
) -> RobotStatus:
    """Get current robot status including position, battery, etc."""
    status = await robot_service.get_status()
    return status

@router.post("/move", response_model=CommandResponse)
async def move_robot(
    command: MoveCommand,
    robot_service: RobotService = Depends(get_robot_service),
    safety_service: SafetyService = Depends(get_safety_service),
    current_user: dict = Depends(get_current_user)
) -> CommandResponse:
    """
    Move the robot with velocity and duration.

    Safety checks are performed before executing the command.
    """
    # Validate safety constraints
    await safety_service.validate_movement(command)

    # Execute movement command (non-blocking)
    result = await robot_service.move(
        linear_velocity=command.linear_velocity,
        angular_velocity=command.angular_velocity,
        duration=command.duration
    )

    return CommandResponse(
        success=True,
        command_id=result.command_id,
        message=f"Robot moving at {command.linear_velocity} m/s for {command.duration}s"
    )

@router.post("/stop", response_model=CommandResponse)
async def stop_robot(
    robot_service: RobotService = Depends(get_robot_service),
    current_user: dict = Depends(get_current_user)
) -> CommandResponse:
    """Immediately stop all robot movement."""
    await robot_service.stop()
    return CommandResponse(
        success=True,
        message="Robot stopped"
    )

@router.post("/head/position", response_model=CommandResponse)
async def set_head_position(
    command: HeadCommand,
    robot_service: RobotService = Depends(get_robot_service),
    current_user: dict = Depends(get_current_user)
) -> CommandResponse:
    """Set robot head pan and tilt angles."""
    result = await robot_service.set_head_position(
        pan=command.pan,
        tilt=command.tilt
    )

    return CommandResponse(
        success=True,
        command_id=result.command_id,
        message=f"Head positioned at pan={command.pan}, tilt={command.tilt}"
    )

@router.post("/led", response_model=CommandResponse)
async def set_led(
    command: LEDCommand,
    robot_service: RobotService = Depends(get_robot_service),
    current_user: dict = Depends(get_current_user)
) -> CommandResponse:
    """Set LED colors and patterns."""
    await robot_service.set_led(
        led_id=command.led_id,
        color=command.color,
        brightness=command.brightness
    )

    return CommandResponse(
        success=True,
        message=f"LED {command.led_id} set to {command.color}"
    )

@router.post("/sequence", response_model=CommandResponse)
async def execute_sequence(
    commands: list[dict],
    background_tasks: BackgroundTasks,
    robot_service: RobotService = Depends(get_robot_service),
    safety_service: SafetyService = Depends(get_safety_service),
    current_user: dict = Depends(get_current_user)
) -> CommandResponse:
    """
    Execute a sequence of commands asynchronously.

    Returns immediately with a sequence ID for tracking.
    """
    sequence_id = await robot_service.create_sequence(commands)

    # Execute sequence in background
    background_tasks.add_task(
        robot_service.execute_sequence,
        sequence_id,
        safety_service
    )

    return CommandResponse(
        success=True,
        command_id=sequence_id,
        message=f"Sequence {sequence_id} queued for execution"
    )

@router.get("/sequence/{sequence_id}/status")
async def get_sequence_status(
    sequence_id: str,
    robot_service: RobotService = Depends(get_robot_service),
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a command sequence."""
    status = await robot_service.get_sequence_status(sequence_id)
    return status
```

### Request/Response Models

**`app/models/requests.py`**:
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Tuple

class MoveCommand(BaseModel):
    """Robot movement command."""
    linear_velocity: float = Field(..., ge=-1.0, le=1.0, description="Linear velocity in m/s")
    angular_velocity: float = Field(..., ge=-2.0, le=2.0, description="Angular velocity in rad/s")
    duration: Optional[float] = Field(None, ge=0, le=60, description="Duration in seconds")

    @validator('linear_velocity', 'angular_velocity')
    def validate_velocity(cls, v):
        """Ensure velocity values are reasonable."""
        if abs(v) > 0 and abs(v) < 0.01:
            raise ValueError("Velocity too small, use 0 or >= 0.01")
        return v

class HeadCommand(BaseModel):
    """Robot head positioning command."""
    pan: float = Field(..., ge=-120, le=120, description="Pan angle in degrees")
    tilt: float = Field(..., ge=-40, le=40, description="Tilt angle in degrees")

class LEDCommand(BaseModel):
    """LED control command."""
    led_id: str = Field(..., description="LED identifier (e.g., 'eye_ring', 'mono')")
    color: Tuple[int, int, int] = Field(..., description="RGB color tuple (0-255)")
    brightness: float = Field(1.0, ge=0.0, le=1.0, description="Brightness 0-1")

    @validator('color')
    def validate_color(cls, v):
        """Validate RGB values."""
        if not all(0 <= c <= 255 for c in v):
            raise ValueError("RGB values must be 0-255")
        return v

class SoundCommand(BaseModel):
    """Sound playback command."""
    sound_file: str = Field(..., description="Sound file name or ID")
    volume: float = Field(1.0, ge=0.0, le=1.0, description="Volume 0-1")
```

**`app/models/responses.py`**:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CommandStatus(str, Enum):
    """Command execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CommandResponse(BaseModel):
    """Standard command response."""
    success: bool
    command_id: Optional[str] = None
    message: str
    timestamp: datetime = datetime.utcnow()
    details: Optional[Dict[str, Any]] = None

class RobotStatus(BaseModel):
    """Robot status information."""
    connected: bool
    battery_level: float
    position: Optional[Dict[str, float]] = None
    pose: Optional[Dict[str, float]] = None
    active_command: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
```

---

## 3. WebSocket Integration for Real-Time Sensor Streaming

### WebSocket Connection Manager

**`app/core/websocket_manager.py`**:
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for real-time sensor data streaming."""

    def __init__(self):
        # Store active connections per client
        self.active_connections: Dict[str, WebSocket] = {}
        # Track subscriptions per connection
        self.subscriptions: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
            self.subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe(self, client_id: str, sensor_type: str) -> None:
        """Subscribe a client to a sensor data stream."""
        async with self._lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id].add(sensor_type)
                logger.info(f"Client {client_id} subscribed to {sensor_type}")

    async def unsubscribe(self, client_id: str, sensor_type: str) -> None:
        """Unsubscribe a client from a sensor data stream."""
        async with self._lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id].discard(sensor_type)
                logger.info(f"Client {client_id} unsubscribed from {sensor_type}")

    async def send_personal_message(self, message: dict, client_id: str) -> None:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                await self.disconnect(client_id)

    async def broadcast_sensor_data(self, sensor_type: str, data: dict) -> None:
        """
        Broadcast sensor data to all subscribed clients.

        Handles disconnections gracefully by removing dead connections.
        """
        message = {
            "type": "sensor_data",
            "sensor": sensor_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Collect clients to disconnect if send fails
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to this sensor
            if sensor_type in self.subscriptions.get(client_id, set()):
                try:
                    await websocket.send_json(message)
                except WebSocketDisconnect:
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    async def broadcast_all(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)

        for client_id in disconnected_clients:
            await self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
```

### WebSocket Endpoints

**`app/api/v1/endpoints/websocket.py`**:
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import asyncio
import logging
import uuid

from app.core.websocket_manager import ConnectionManager
from app.services.sensor_service import SensorService
from app.dependencies import get_sensor_service
from app.core.security import verify_ws_token

router = APIRouter(prefix="/ws", tags=["websocket"])

# Global WebSocket manager (can also be in app state)
ws_manager = ConnectionManager()

@router.websocket("/sensors")
async def websocket_sensor_stream(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time sensor data streaming.

    Protocol:
    - Client sends: {"action": "subscribe", "sensor": "accelerometer"}
    - Client sends: {"action": "unsubscribe", "sensor": "accelerometer"}
    - Server sends: {"type": "sensor_data", "sensor": "...", "data": {...}}
    """
    client_id = str(uuid.uuid4())

    # Verify authentication
    if token:
        user = await verify_ws_token(token)
        if not user:
            await websocket.close(code=1008, reason="Unauthorized")
            return

    await ws_manager.connect(websocket, client_id)

    try:
        # Send welcome message
        await ws_manager.send_personal_message(
            {
                "type": "connected",
                "client_id": client_id,
                "message": "Connected to sensor stream"
            },
            client_id
        )

        # Listen for client messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            action = data.get("action")
            sensor = data.get("sensor")

            if action == "subscribe" and sensor:
                await ws_manager.subscribe(client_id, sensor)
                await ws_manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "sensor": sensor,
                        "message": f"Subscribed to {sensor}"
                    },
                    client_id
                )

            elif action == "unsubscribe" and sensor:
                await ws_manager.unsubscribe(client_id, sensor)
                await ws_manager.send_personal_message(
                    {
                        "type": "unsubscribed",
                        "sensor": sensor,
                        "message": f"Unsubscribed from {sensor}"
                    },
                    client_id
                )

            elif action == "ping":
                await ws_manager.send_personal_message(
                    {"type": "pong"},
                    client_id
                )

    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logging.error(f"WebSocket error for client {client_id}: {e}")
        await ws_manager.disconnect(client_id)

@router.get("/connections")
async def get_connection_info():
    """Get information about active WebSocket connections."""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "timestamp": asyncio.get_event_loop().time()
    }
```

### Sensor Streaming Service

**`app/services/sensor_service.py`**:
```python
from typing import Dict, Any, Optional, Callable
import asyncio
import logging

from app.hardware.robot_interface import RobotInterface
from app.config import settings

logger = logging.getLogger(__name__)

class SensorService:
    """Service for managing sensor data polling and streaming."""

    def __init__(self, robot: RobotInterface):
        self.robot = robot
        self.polling_tasks: Dict[str, asyncio.Task] = {}
        self.sensor_callbacks: Dict[str, list[Callable]] = {}
        self._polling = False

    async def start_polling(self, sensor_type: str, callback: Callable) -> None:
        """Start polling a sensor and call the callback with new data."""
        if sensor_type in self.polling_tasks:
            logger.warning(f"Polling already active for {sensor_type}")
            return

        # Register callback
        if sensor_type not in self.sensor_callbacks:
            self.sensor_callbacks[sensor_type] = []
        self.sensor_callbacks[sensor_type].append(callback)

        # Create polling task
        task = asyncio.create_task(
            self._poll_sensor(sensor_type)
        )
        self.polling_tasks[sensor_type] = task
        logger.info(f"Started polling {sensor_type}")

    async def stop_polling(self, sensor_type: str) -> None:
        """Stop polling a sensor."""
        if sensor_type in self.polling_tasks:
            task = self.polling_tasks[sensor_type]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.polling_tasks[sensor_type]
            logger.info(f"Stopped polling {sensor_type}")

    async def _poll_sensor(self, sensor_type: str) -> None:
        """Internal method to continuously poll a sensor."""
        interval = settings.SENSOR_POLL_INTERVAL

        while True:
            try:
                # Read sensor data (this may be a blocking operation)
                data = await asyncio.to_thread(
                    self.robot.read_sensor,
                    sensor_type
                )

                # Call all registered callbacks
                if sensor_type in self.sensor_callbacks:
                    for callback in self.sensor_callbacks[sensor_type]:
                        try:
                            await callback(sensor_type, data)
                        except Exception as e:
                            logger.error(f"Error in sensor callback: {e}")

                # Wait before next poll
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error polling {sensor_type}: {e}")
                await asyncio.sleep(interval)

    async def get_sensor_data(self, sensor_type: str) -> Dict[str, Any]:
        """Get current sensor data (single read)."""
        data = await asyncio.to_thread(
            self.robot.read_sensor,
            sensor_type
        )
        return data

    async def cleanup(self) -> None:
        """Stop all polling tasks."""
        for sensor_type in list(self.polling_tasks.keys()):
            await self.stop_polling(sensor_type)
```

---

## 4. Background Task Management for Sensor Polling

### Background Task Patterns

For robotics control, there are different patterns for background processing:

1. **FastAPI BackgroundTasks** - For lightweight, short-lived tasks
2. **asyncio Tasks** - For long-running sensor polling
3. **Celery + RabbitMQ** - For heavy computation and distributed tasks

### Pattern 1: FastAPI BackgroundTasks (Lightweight)

```python
from fastapi import BackgroundTasks

@router.post("/calibrate")
async def calibrate_robot(
    background_tasks: BackgroundTasks,
    robot_service: RobotService = Depends(get_robot_service)
):
    """Start robot calibration in background."""

    def calibrate():
        """Calibration process."""
        robot_service.calibrate_sensors()
        logger.info("Calibration complete")

    background_tasks.add_task(calibrate)

    return {"message": "Calibration started"}
```

**Limitations**:
- No built-in task cancellation
- Tasks die if the worker restarts
- Not suitable for long-running or mission-critical operations

### Pattern 2: Managed AsyncIO Tasks (Recommended for Sensor Polling)

**`app/hardware/sensor_manager.py`**:
```python
import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class SensorReading:
    """Sensor reading data structure."""
    sensor_type: str
    data: dict
    timestamp: datetime

class SensorManager:
    """
    Manages continuous sensor polling with asyncio tasks.

    Provides task lifecycle management, error handling, and graceful shutdown.
    """

    def __init__(self, robot_interface):
        self.robot = robot_interface
        self.tasks: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, list[Callable]] = {}
        self.polling_intervals: Dict[str, float] = {}
        self._shutdown_event = asyncio.Event()

    async def start_sensor_polling(
        self,
        sensor_type: str,
        interval: float,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Start polling a specific sensor.

        Args:
            sensor_type: Type of sensor (e.g., 'accelerometer', 'distance')
            interval: Polling interval in seconds
            callback: Optional callback function for sensor data
        """
        if sensor_type in self.tasks:
            logger.warning(f"Sensor {sensor_type} already polling")
            return

        self.polling_intervals[sensor_type] = interval

        if callback:
            if sensor_type not in self.callbacks:
                self.callbacks[sensor_type] = []
            self.callbacks[sensor_type].append(callback)

        # Create and store the task
        task = asyncio.create_task(
            self._poll_sensor_loop(sensor_type, interval)
        )
        self.tasks[sensor_type] = task
        logger.info(f"Started polling {sensor_type} at {interval}s interval")

    async def stop_sensor_polling(self, sensor_type: str) -> None:
        """Stop polling a specific sensor."""
        if sensor_type not in self.tasks:
            logger.warning(f"Sensor {sensor_type} not currently polling")
            return

        task = self.tasks[sensor_type]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            logger.info(f"Stopped polling {sensor_type}")

        del self.tasks[sensor_type]
        if sensor_type in self.polling_intervals:
            del self.polling_intervals[sensor_type]

    async def _poll_sensor_loop(self, sensor_type: str, interval: float) -> None:
        """
        Internal polling loop for a sensor.

        Handles errors gracefully and continues polling.
        """
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self._shutdown_event.is_set():
            try:
                # Read sensor (offload blocking I/O to thread pool)
                data = await asyncio.to_thread(
                    self.robot.read_sensor,
                    sensor_type
                )

                # Create reading object
                reading = SensorReading(
                    sensor_type=sensor_type,
                    data=data,
                    timestamp=datetime.utcnow()
                )

                # Invoke callbacks
                if sensor_type in self.callbacks:
                    for callback in self.callbacks[sensor_type]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(reading)
                            else:
                                callback(reading)
                        except Exception as e:
                            logger.error(f"Callback error for {sensor_type}: {e}")

                # Reset error counter on success
                consecutive_errors = 0

                # Wait for next poll
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"Polling cancelled for {sensor_type}")
                break

            except Exception as e:
                consecutive_errors += 1
                logger.error(
                    f"Error polling {sensor_type} ({consecutive_errors}/{max_consecutive_errors}): {e}"
                )

                # Stop polling if too many consecutive errors
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(
                        f"Max consecutive errors reached for {sensor_type}, stopping poll"
                    )
                    break

                # Back off on error
                await asyncio.sleep(interval * 2)

    async def shutdown(self) -> None:
        """Gracefully shutdown all sensor polling tasks."""
        logger.info("Shutting down sensor manager...")
        self._shutdown_event.set()

        # Cancel all tasks
        for sensor_type in list(self.tasks.keys()):
            await self.stop_sensor_polling(sensor_type)

        logger.info("Sensor manager shutdown complete")

    def get_active_sensors(self) -> list[str]:
        """Get list of currently polling sensors."""
        return list(self.tasks.keys())
```

### Pattern 3: Celery for Heavy Processing

For computationally intensive tasks (e.g., path planning, computer vision), use Celery:

**`app/celery_app.py`**:
```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "robot_tasks",
    broker=settings.CELERY_BROKER_URL,  # e.g., "amqp://rabbitmq:5672"
    backend=settings.CELERY_RESULT_BACKEND  # e.g., "redis://redis:6379"
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
)
```

**`app/tasks/robot_tasks.py`**:
```python
from app.celery_app import celery_app
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="tasks.compute_path")
def compute_path(self, start: Dict[str, float], goal: Dict[str, float], obstacles: list) -> Dict[str, Any]:
    """
    Compute navigation path using A* or similar algorithm.

    This is CPU-intensive and suitable for Celery.
    """
    self.update_state(state='PROGRESS', meta={'progress': 0})

    try:
        # Path planning algorithm
        path = run_path_planning_algorithm(start, goal, obstacles)

        self.update_state(state='PROGRESS', meta={'progress': 100})

        return {
            "path": path,
            "distance": calculate_path_distance(path),
            "estimated_time": estimate_travel_time(path)
        }
    except Exception as e:
        logger.error(f"Path planning error: {e}")
        raise

@celery_app.task(name="tasks.process_sensor_batch")
def process_sensor_batch(sensor_data: list[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process a batch of sensor readings for analytics.

    Examples: filtering, aggregation, anomaly detection.
    """
    # Processing logic
    processed = {
        "count": len(sensor_data),
        "statistics": compute_statistics(sensor_data),
        "anomalies": detect_anomalies(sensor_data)
    }

    return processed
```

**Using Celery tasks**:
```python
from app.tasks.robot_tasks import compute_path

@router.post("/navigate")
async def plan_navigation(
    start: Dict[str, float],
    goal: Dict[str, float],
    obstacles: list
):
    """Plan navigation path asynchronously using Celery."""

    # Queue task
    task = compute_path.delay(start, goal, obstacles)

    return {
        "task_id": task.id,
        "status": "queued",
        "message": "Path computation started"
    }

@router.get("/navigate/status/{task_id}")
async def get_navigation_status(task_id: str):
    """Check status of path planning task."""
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {"status": "pending"}
    elif task.state == 'PROGRESS':
        response = {
            "status": "in_progress",
            "progress": task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            "status": "completed",
            "result": task.result
        }
    else:
        response = {
            "status": "failed",
            "error": str(task.info)
        }

    return response
```

---

## 5. Error Handling and Safety Mechanisms

### Custom Exception Hierarchy

**`app/core/exceptions.py`**:
```python
from fastapi import HTTPException, status

class RobotException(HTTPException):
    """Base exception for robot-related errors."""

    def __init__(self, message: str, status_code: int = 500, error_type: str = "ROBOT_ERROR", details: dict = None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)

class SafetyException(RobotException):
    """Exception for safety-critical violations."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="SAFETY_VIOLATION",
            details=details
        )

class HardwareException(RobotException):
    """Exception for hardware communication errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="HARDWARE_ERROR",
            details=details
        )

class CommandException(RobotException):
    """Exception for invalid command parameters."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="INVALID_COMMAND",
            details=details
        )

class ConnectionException(RobotException):
    """Exception for robot connection issues."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="CONNECTION_ERROR",
            details=details
        )
```

### Safety Service Implementation

**`app/services/safety_service.py`**:
```python
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.exceptions import SafetyException
from app.models.requests import MoveCommand
from app.config import settings

logger = logging.getLogger(__name__)

class SafetyService:
    """
    Safety service for validating robot commands and monitoring safety constraints.

    Implements safety checks including:
    - Velocity limits
    - Obstacle detection
    - Battery level monitoring
    - Emergency stop conditions
    """

    def __init__(self):
        self.emergency_stop_active = False
        self.safety_violations: list[Dict[str, Any]] = []
        self.last_obstacle_check: Optional[datetime] = None

    async def validate_movement(self, command: MoveCommand) -> None:
        """
        Validate movement command against safety constraints.

        Raises SafetyException if command violates safety rules.
        """
        # Check if emergency stop is active
        if self.emergency_stop_active:
            raise SafetyException(
                "Emergency stop is active, movement commands are disabled",
                details={"command": command.dict()}
            )

        # Validate velocity limits
        if abs(command.linear_velocity) > settings.MAX_VELOCITY:
            raise SafetyException(
                f"Linear velocity {command.linear_velocity} exceeds max {settings.MAX_VELOCITY}",
                details={
                    "requested_velocity": command.linear_velocity,
                    "max_velocity": settings.MAX_VELOCITY
                }
            )

        # Additional safety checks can be added here
        logger.debug(f"Movement command validated: {command}")

    async def check_obstacle_proximity(self, distance_data: Dict[str, float]) -> bool:
        """
        Check if obstacles are too close.

        Returns True if safe, raises SafetyException if obstacles detected.
        """
        self.last_obstacle_check = datetime.utcnow()

        min_distance = min(distance_data.values()) if distance_data else float('inf')

        if min_distance < settings.MIN_OBSTACLE_DISTANCE:
            violation = {
                "type": "OBSTACLE_TOO_CLOSE",
                "distance": min_distance,
                "threshold": settings.MIN_OBSTACLE_DISTANCE,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.safety_violations.append(violation)

            raise SafetyException(
                f"Obstacle detected at {min_distance}m (minimum: {settings.MIN_OBSTACLE_DISTANCE}m)",
                details=violation
            )

        return True

    async def check_battery_level(self, battery_level: float) -> bool:
        """
        Check if battery level is sufficient.

        Warns if low, raises exception if critical.
        """
        CRITICAL_BATTERY = 10.0
        LOW_BATTERY = 20.0

        if battery_level < CRITICAL_BATTERY:
            raise SafetyException(
                f"Critical battery level: {battery_level}%",
                details={"battery_level": battery_level}
            )

        if battery_level < LOW_BATTERY:
            logger.warning(f"Low battery level: {battery_level}%")

        return True

    def activate_emergency_stop(self) -> None:
        """Activate emergency stop mode."""
        self.emergency_stop_active = True
        logger.critical("EMERGENCY STOP ACTIVATED")

        violation = {
            "type": "EMERGENCY_STOP",
            "timestamp": datetime.utcnow().isoformat(),
            "reason": "Manual emergency stop"
        }
        self.safety_violations.append(violation)

    def deactivate_emergency_stop(self) -> None:
        """Deactivate emergency stop mode (requires manual confirmation)."""
        self.emergency_stop_active = False
        logger.info("Emergency stop deactivated")

    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        return {
            "emergency_stop_active": self.emergency_stop_active,
            "recent_violations": self.safety_violations[-10:],  # Last 10
            "last_obstacle_check": self.last_obstacle_check.isoformat() if self.last_obstacle_check else None
        }
```

### Global Error Handling Middleware

**`app/middleware/error_handler.py`**:
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            # Log the full exception
            logger.error(
                f"Unhandled exception: {exc}\n{traceback.format_exc()}"
            )

            # Return structured error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path
                }
            )

# Add to main.py
# app.add_middleware(ErrorHandlingMiddleware)
```

---

## 6. Authentication and Security

### JWT-Based Authentication

**`app/core/security.py`**:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Dictionary containing user information
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

async def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token.

    Returns:
        User data from token, or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None

        return {"username": username, "payload": payload}

    except JWTError:
        return None

async def verify_ws_token(token: str) -> Optional[dict]:
    """Verify token for WebSocket connections."""
    return await verify_token(token)
```

### Authentication Endpoints

**`app/api/v1/endpoints/auth.py`**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional

from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash
)
from app.config import settings
from app.models.auth import Token, User

router = APIRouter(prefix="/auth", tags=["authentication"])

# Mock user database (replace with real database)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@robot.com",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin"
    }
}

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    OAuth2 compatible token login.

    Get an access token for future requests.
    """
    user = fake_users_db.get(form_data.username)

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)) -> User:
    """Get current user information."""
    username = current_user["username"]
    user = fake_users_db.get(username)

    return User(
        username=user["username"],
        email=user["email"],
        role=user["role"]
    )
```

**`app/models/auth.py`**:
```python
from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    """User model."""
    username: str
    email: EmailStr
    role: str
    disabled: bool = False
```

### Role-Based Access Control (RBAC)

```python
from functools import wraps
from fastapi import HTTPException, status, Depends

def require_role(required_role: str):
    """Decorator to require specific role for endpoint access."""

    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("payload", {}).get("role")

        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )

        return current_user

    return role_checker

# Usage in endpoints
@router.post("/emergency-stop")
async def emergency_stop(
    current_user: dict = Depends(require_role("operator"))
):
    """Emergency stop - requires operator role."""
    # Implementation
    pass
```

---

## 7. Rate Limiting and Request Queuing

### Rate Limiting with SlowAPI

**Install**: `pip install slowapi`

**`app/middleware/rate_limiter.py`**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"]
)

# Add to main.py:
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# app.add_middleware(SlowAPIMiddleware)
```

**Usage in endpoints**:
```python
from app.middleware.rate_limiter import limiter

@router.post("/move")
@limiter.limit("10/second")  # Max 10 movement commands per second
async def move_robot(
    request: Request,
    command: MoveCommand,
    robot_service: RobotService = Depends(get_robot_service)
):
    """Move robot with rate limiting."""
    result = await robot_service.move(command)
    return result
```

### Custom Rate Limiter with Redis

**`app/core/redis_rate_limiter.py`**:
```python
import redis.asyncio as redis
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    """
    Token bucket rate limiter using Redis.

    Provides per-user and per-endpoint rate limiting.
    """

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            key: Unique identifier (e.g., user_id, IP address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            (allowed, remaining_requests)
        """
        current_time = datetime.utcnow().timestamp()
        window_key = f"rate_limit:{key}:{int(current_time // window_seconds)}"

        async with self.redis.pipeline() as pipe:
            try:
                # Increment counter
                await pipe.incr(window_key)
                # Set expiration
                await pipe.expire(window_key, window_seconds * 2)
                results = await pipe.execute()

                request_count = results[0]

                if request_count > max_requests:
                    return False, 0

                remaining = max_requests - request_count
                return True, remaining

            except Exception as e:
                logger.error(f"Rate limit check error: {e}")
                # Fail open - allow request if Redis is unavailable
                return True, max_requests

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()
```

### Hardware Command Queue

For hardware operations that must be executed sequentially:

**`app/services/command_queue.py`**:
```python
import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)

class CommandPriority(Enum):
    """Command priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    EMERGENCY = 3

@dataclass
class QueuedCommand:
    """Represents a queued robot command."""
    id: str
    command_type: str
    parameters: Dict[str, Any]
    priority: CommandPriority
    timestamp: datetime
    callback: Optional[Callable] = None

class CommandQueue:
    """
    Priority queue for robot commands.

    Ensures commands are executed sequentially and in priority order.
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_size)
        self.processing_task: Optional[asyncio.Task] = None
        self.current_command: Optional[QueuedCommand] = None
        self.command_history: list[QueuedCommand] = []
        self._shutdown = False

    async def enqueue(
        self,
        command_type: str,
        parameters: Dict[str, Any],
        priority: CommandPriority = CommandPriority.NORMAL,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Add command to queue.

        Returns:
            Command ID for tracking
        """
        command = QueuedCommand(
            id=str(uuid.uuid4()),
            command_type=command_type,
            parameters=parameters,
            priority=priority,
            timestamp=datetime.utcnow(),
            callback=callback
        )

        # Priority queue uses tuple (priority, item)
        # Lower number = higher priority, so negate enum value
        await self.queue.put((-priority.value, command))

        logger.info(f"Command {command.id} queued with priority {priority.name}")
        return command.id

    async def start_processing(self, executor: Callable) -> None:
        """
        Start processing commands from the queue.

        Args:
            executor: Async function that executes commands
        """
        if self.processing_task is not None:
            logger.warning("Command processing already started")
            return

        self.processing_task = asyncio.create_task(
            self._process_queue(executor)
        )
        logger.info("Command queue processing started")

    async def _process_queue(self, executor: Callable) -> None:
        """Internal queue processing loop."""
        while not self._shutdown:
            try:
                # Get next command (blocks until available)
                priority, command = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )

                self.current_command = command
                logger.info(f"Executing command {command.id}: {command.command_type}")

                try:
                    # Execute command
                    result = await executor(command)

                    # Call callback if provided
                    if command.callback:
                        await command.callback(result)

                    # Add to history
                    self.command_history.append(command)

                except Exception as e:
                    logger.error(f"Error executing command {command.id}: {e}")

                finally:
                    self.current_command = None
                    self.queue.task_done()

            except asyncio.TimeoutError:
                # No commands in queue, continue waiting
                continue

            except Exception as e:
                logger.error(f"Queue processing error: {e}")

    async def clear_queue(self) -> int:
        """
        Clear all pending commands.

        Returns:
            Number of commands cleared
        """
        count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
                count += 1
            except asyncio.QueueEmpty:
                break

        logger.info(f"Cleared {count} commands from queue")
        return count

    async def shutdown(self) -> None:
        """Stop queue processing and clear pending commands."""
        logger.info("Shutting down command queue...")
        self._shutdown = True

        if self.processing_task:
            await self.processing_task

        await self.clear_queue()
        logger.info("Command queue shutdown complete")

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    def get_status(self) -> Dict[str, Any]:
        """Get queue status information."""
        return {
            "queue_size": self.queue.qsize(),
            "current_command": self.current_command.command_type if self.current_command else None,
            "history_size": len(self.command_history)
        }
```

**Integration with Robot Service**:
```python
from app.services.command_queue import CommandQueue, CommandPriority

class RobotService:
    def __init__(self, robot: RobotInterface):
        self.robot = robot
        self.command_queue = CommandQueue(max_size=100)

    async def initialize(self):
        """Start command queue processing."""
        await self.command_queue.start_processing(self._execute_command)

    async def _execute_command(self, command: QueuedCommand) -> Dict[str, Any]:
        """Execute a robot command."""
        if command.command_type == "move":
            return await self.robot.move(**command.parameters)
        elif command.command_type == "stop":
            return await self.robot.stop()
        # ... other command types

    async def move(self, linear_velocity: float, angular_velocity: float, duration: float = None):
        """Queue a move command."""
        command_id = await self.command_queue.enqueue(
            command_type="move",
            parameters={
                "linear_velocity": linear_velocity,
                "angular_velocity": angular_velocity,
                "duration": duration
            },
            priority=CommandPriority.NORMAL
        )
        return {"command_id": command_id}

    async def emergency_stop(self):
        """Emergency stop with highest priority."""
        # Clear queue and execute immediately
        await self.command_queue.clear_queue()

        command_id = await self.command_queue.enqueue(
            command_type="stop",
            parameters={},
            priority=CommandPriority.EMERGENCY
        )
        return {"command_id": command_id}
```

---

## 8. Async Patterns for Non-Blocking Hardware Operations

### Understanding Async in FastAPI for Hardware Control

**Key Principles**:

1. **Use `async def` for I/O-bound operations** (network, database, file I/O)
2. **Use `def` for CPU-bound or blocking operations** (FastAPI runs these in a thread pool)
3. **Never call blocking functions directly in async functions** (blocks the event loop)
4. **Use `asyncio.to_thread()` to offload blocking calls**

### Pattern 1: Hardware Interface with Thread Pool

**`app/hardware/robot_interface.py`**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class RobotInterface(ABC):
    """
    Abstract interface for robot hardware control.

    Implements async wrappers around blocking hardware operations.
    """

    @abstractmethod
    def _read_sensor_blocking(self, sensor_type: str) -> Dict[str, Any]:
        """Blocking sensor read (runs in thread pool)."""
        pass

    @abstractmethod
    def _send_command_blocking(self, command: str, params: Dict[str, Any]) -> bool:
        """Blocking command send (runs in thread pool)."""
        pass

    async def read_sensor(self, sensor_type: str) -> Dict[str, Any]:
        """
        Async wrapper for sensor reading.

        Offloads blocking I/O to thread pool.
        """
        try:
            data = await asyncio.to_thread(
                self._read_sensor_blocking,
                sensor_type
            )
            return data
        except Exception as e:
            logger.error(f"Error reading sensor {sensor_type}: {e}")
            raise HardwareException(f"Failed to read sensor: {sensor_type}")

    async def send_command(self, command: str, params: Dict[str, Any]) -> bool:
        """
        Async wrapper for command sending.

        Offloads blocking I/O to thread pool.
        """
        try:
            success = await asyncio.to_thread(
                self._send_command_blocking,
                command,
                params
            )
            return success
        except Exception as e:
            logger.error(f"Error sending command {command}: {e}")
            raise HardwareException(f"Failed to send command: {command}")
```

### Pattern 2: Concrete Implementation for WonderPy

**`app/hardware/dash_robot.py`**:
```python
from typing import Dict, Any, Optional
import WonderPy.core.wwMain as wwMain
from WonderPy.core.wwConstants import WWRobotConstants
import logging

from app.hardware.robot_interface import RobotInterface
from app.core.exceptions import HardwareException

logger = logging.getLogger(__name__)

class DashRobot(RobotInterface):
    """
    Concrete implementation for Dash robot using WonderPy.

    Wraps WonderPy's blocking API with async interface.
    """

    def __init__(self):
        self.robot = None
        self._connected = False

    def _connect_blocking(self) -> bool:
        """Blocking connection to robot."""
        try:
            # WonderPy connection logic
            self.robot = wwMain.connect_to_default_robot()
            if self.robot:
                self._connected = True
                logger.info(f"Connected to robot: {self.robot.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def connect(self) -> bool:
        """Async connection to robot."""
        return await asyncio.to_thread(self._connect_blocking)

    def _disconnect_blocking(self) -> None:
        """Blocking disconnection."""
        if self.robot:
            wwMain.disconnect(self.robot)
            self._connected = False
            logger.info("Disconnected from robot")

    async def disconnect(self) -> None:
        """Async disconnection."""
        await asyncio.to_thread(self._disconnect_blocking)

    def _read_sensor_blocking(self, sensor_type: str) -> Dict[str, Any]:
        """Read sensor data (blocking)."""
        if not self._connected or not self.robot:
            raise HardwareException("Robot not connected")

        try:
            if sensor_type == "accelerometer":
                sensor = self.robot.sensors.accelerometer
                return {
                    "x": sensor.x,
                    "y": sensor.y,
                    "z": sensor.z
                }

            elif sensor_type == "distance":
                sensor = self.robot.sensors.distance
                return {
                    "front": sensor.front,
                    "back": sensor.back
                }

            elif sensor_type == "pose":
                sensor = self.robot.sensors.pose
                return {
                    "x": sensor.x,
                    "y": sensor.y,
                    "angle": sensor.angle
                }

            else:
                raise HardwareException(f"Unknown sensor type: {sensor_type}")

        except AttributeError as e:
            logger.error(f"Sensor read error: {e}")
            raise HardwareException(f"Sensor not available: {sensor_type}")

    def _send_command_blocking(self, command: str, params: Dict[str, Any]) -> bool:
        """Send command to robot (blocking)."""
        if not self._connected or not self.robot:
            raise HardwareException("Robot not connected")

        try:
            if command == "move":
                linear = params.get("linear_velocity", 0)
                angular = params.get("angular_velocity", 0)
                duration = params.get("duration")

                # Convert to WonderPy units
                left_speed = linear - angular
                right_speed = linear + angular

                self.robot.commands.body.do_wheels(
                    left_speed,
                    right_speed,
                    duration if duration else 0
                )
                return True

            elif command == "stop":
                self.robot.commands.body.do_wheels(0, 0, 0)
                return True

            elif command == "head":
                pan = params.get("pan", 0)
                tilt = params.get("tilt", 0)

                self.robot.commands.head.do_pan_tilt(pan, tilt)
                return True

            elif command == "led":
                led_id = params.get("led_id")
                color = params.get("color", (0, 0, 0))
                brightness = params.get("brightness", 1.0)

                if led_id == "eye_ring":
                    r, g, b = color
                    self.robot.commands.eyering.do_mono(
                        r, g, b, brightness
                    )
                return True

            else:
                raise HardwareException(f"Unknown command: {command}")

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise HardwareException(f"Failed to execute command: {command}")
```

### Pattern 3: Concurrent Operations with asyncio.gather()

```python
async def get_all_sensor_data(robot: RobotInterface) -> Dict[str, Any]:
    """
    Read multiple sensors concurrently.

    Uses asyncio.gather() to parallelize sensor reads.
    """
    # Run all sensor reads concurrently
    accel_data, distance_data, pose_data = await asyncio.gather(
        robot.read_sensor("accelerometer"),
        robot.read_sensor("distance"),
        robot.read_sensor("pose"),
        return_exceptions=True  # Don't fail all if one fails
    )

    # Handle potential errors
    result = {}

    if not isinstance(accel_data, Exception):
        result["accelerometer"] = accel_data

    if not isinstance(distance_data, Exception):
        result["distance"] = distance_data

    if not isinstance(pose_data, Exception):
        result["pose"] = pose_data

    return result
```

### Pattern 4: Timeout and Cancellation

```python
async def move_with_timeout(
    robot: RobotInterface,
    linear_velocity: float,
    angular_velocity: float,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Execute movement command with timeout.

    Automatically cancels if it takes too long.
    """
    try:
        result = await asyncio.wait_for(
            robot.send_command("move", {
                "linear_velocity": linear_velocity,
                "angular_velocity": angular_velocity
            }),
            timeout=timeout
        )
        return {"success": True, "result": result}

    except asyncio.TimeoutError:
        logger.error(f"Movement command timed out after {timeout}s")
        # Send stop command
        await robot.send_command("stop", {})
        raise HardwareException(f"Command timed out after {timeout}s")
```

### Pattern 5: Proper Event Loop Usage

```python
# WRONG - Don't do this in async context
def bad_async_pattern():
    # This creates a new event loop and blocks
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(some_async_function())
    return result

# RIGHT - Use await
async def good_async_pattern():
    result = await some_async_function()
    return result

# For running blocking code in async context
async def run_blocking_safely():
    # Option 1: Use to_thread for I/O bound
    result = await asyncio.to_thread(blocking_io_function)

    # Option 2: Use run_in_executor for CPU bound
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, cpu_intensive_function)

    return result
```

---

## 9. Complete Reference Architecture

### Full System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  (Web Dashboard, Mobile App, External Services)                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ HTTPS/WSS
             │
┌────────────▼────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                │
│              (nginx, Traefik, or AWS ALB)                       │
└────────────┬────────────────────────────────────────────────────┘
             │
             │
┌────────────▼────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                                                                  │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │  REST Endpoints  │      │  WebSocket       │                │
│  │  (/api/v1/...)   │      │  (/ws/sensors)   │                │
│  └────────┬─────────┘      └────────┬─────────┘                │
│           │                         │                           │
│  ┌────────▼─────────────────────────▼─────────┐                │
│  │        Middleware Layer                     │                │
│  │  - Authentication (JWT)                     │                │
│  │  - Rate Limiting                            │                │
│  │  - Error Handling                           │                │
│  │  - Logging                                  │                │
│  └────────┬────────────────────────────────────┘                │
│           │                                                      │
│  ┌────────▼────────────────────────────────────┐                │
│  │        Service Layer                        │                │
│  │  - Robot Service (commands)                 │                │
│  │  - Sensor Service (polling)                 │                │
│  │  - Safety Service (validation)              │                │
│  │  - Command Queue                            │                │
│  └────────┬────────────────────────────────────┘                │
│           │                                                      │
│  ┌────────▼────────────────────────────────────┐                │
│  │     Hardware Abstraction Layer              │                │
│  │  - Robot Interface (abstract)               │                │
│  │  - Dash Robot Implementation                │                │
│  │  - Connection Manager                       │                │
│  │  - Sensor Manager                           │                │
│  └────────┬────────────────────────────────────┘                │
└───────────┼──────────────────────────────────────────────────────┘
            │
            │ Bluetooth LE / Serial / Network
            │
┌───────────▼──────────────────────────────────────────────────────┐
│                    Physical Robot Hardware                       │
│               (Dash, Dot, Cue, or Custom Robot)                  │
└──────────────────────────────────────────────────────────────────┘

External Services:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Redis      │    │   RabbitMQ   │    │  PostgreSQL  │
│ (Rate Limit, │    │  (Celery     │    │  (Metrics,   │
│  Cache)      │    │   Broker)    │    │   Logs)      │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Docker Compose Setup

**`docker-compose.yml`**:
```yaml
version: '3.8'

services:
  # FastAPI Application
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - CELERY_BROKER_URL=amqp://rabbitmq:5672
      - DATABASE_URL=postgresql://postgres:password@db:5432/robot_db
    depends_on:
      - redis
      - rabbitmq
      - db
    volumes:
      - ./app:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Redis for caching and rate limiting
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # RabbitMQ for Celery
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=admin

  # Celery Worker
  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - CELERY_BROKER_URL=amqp://rabbitmq:5672
      - CELERY_RESULT_BACKEND=redis://redis:6379
    depends_on:
      - rabbitmq
      - redis
    volumes:
      - ./app:/app

  # Celery Flower (monitoring)
  flower:
    build: .
    command: celery -A app.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=amqp://rabbitmq:5672
    depends_on:
      - rabbitmq
      - redis

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=robot_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Requirements File

**`requirements.txt`**:
```txt
# FastAPI
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Pydantic
pydantic==2.5.3
pydantic-settings==2.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1

# Redis
redis==5.0.1

# Celery
celery==5.3.6
flower==2.0.1

# WebSocket
websockets==12.0

# Rate Limiting
slowapi==0.1.9

# HTTP Client
httpx==0.26.0
aiohttp==3.9.1

# Utilities
python-dotenv==1.0.0
loguru==0.7.2

# Robot Hardware (example - adjust for your robot)
# WonderPy (for Dash/Dot/Cue robots)
# pyserial (for serial communication)
# RPi.GPIO (for Raspberry Pi GPIO)
```

---

## Summary and Key Takeaways

### Best Practices Checklist

1. **Architecture**:
   - ✅ Use layered architecture (API, Service, Hardware layers)
   - ✅ Implement dependency injection for loose coupling
   - ✅ Abstract hardware interfaces for testability

2. **API Design**:
   - ✅ Version your API (e.g., /api/v1/)
   - ✅ Use Pydantic models for validation
   - ✅ Implement idempotent commands where possible
   - ✅ Return structured responses with timestamps

3. **Real-Time Communication**:
   - ✅ Use WebSocket for sensor streaming
   - ✅ Implement connection manager for multiple clients
   - ✅ Handle disconnections gracefully
   - ✅ Use subscription model for selective data streaming

4. **Background Processing**:
   - ✅ Use asyncio tasks for continuous sensor polling
   - ✅ Implement graceful shutdown for background tasks
   - ✅ Use Celery for heavy computation
   - ✅ Monitor task health and restart on failure

5. **Safety**:
   - ✅ Implement safety service with validation
   - ✅ Create custom exception hierarchy
   - ✅ Add emergency stop functionality
   - ✅ Log all safety violations

6. **Security**:
   - ✅ Use JWT authentication
   - ✅ Implement role-based access control
   - ✅ Secure WebSocket connections
   - ✅ Validate all inputs

7. **Rate Limiting**:
   - ✅ Implement per-endpoint rate limits
   - ✅ Use priority queue for command ordering
   - ✅ Handle queue overflow gracefully

8. **Async Patterns**:
   - ✅ Use async def for I/O-bound operations
   - ✅ Offload blocking calls to thread pool
   - ✅ Never block the event loop
   - ✅ Use timeouts and cancellation

### Performance Considerations

- **Sensor Polling**: 10-100Hz is typical (0.01-0.1s interval)
- **WebSocket Messages**: Limit to necessary data, use compression
- **Command Queue**: Keep size reasonable (< 1000 commands)
- **Rate Limiting**: Adjust based on hardware capabilities
- **Thread Pool**: Starlette default is 40 threads per worker

### Production Deployment

1. Use **multiple Uvicorn workers** behind a load balancer
2. Implement **health checks** and **readiness probes**
3. Use **Redis** for distributed rate limiting and caching
4. Set up **monitoring** (Prometheus, Grafana)
5. Implement **logging** (structured JSON logs)
6. Use **Docker** and **Kubernetes** for orchestration

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **FastAPI Best Practices**: https://github.com/zhanymkanov/fastapi-best-practices
- **Async Programming**: https://realpython.com/async-io-python/
- **Robot Operating System (ROS)**: https://www.ros.org/ (for advanced robotics)
- **WebSocket Protocol**: https://datatracker.ietf.org/doc/html/rfc6455

---

**Document Version**: 1.0
**Last Updated**: 2025-01-08
**Author**: Research compiled from industry best practices
