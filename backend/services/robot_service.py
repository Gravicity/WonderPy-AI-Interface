"""
Robot Service - Hardware Abstraction Layer
Provides interface to Dash robot via WonderPy with mock implementation for testing
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class SensorData:
    """Robot sensor readings"""
    timestamp: datetime

    # Distance sensors (cm)
    distance_front_left: float
    distance_front_right: float
    distance_rear: float

    # Accelerometer (cm/s²)
    accel_x: float
    accel_y: float
    accel_z: float

    # Gyroscope (degrees/s)
    gyro_x: float
    gyro_y: float
    gyro_z: float

    # Pose
    pose_x: float
    pose_y: float
    pose_theta: float  # degrees

    # Battery
    battery_level: int  # 0-100%

    # Buttons
    button_1_pressed: bool
    button_2_pressed: bool
    button_3_pressed: bool


@dataclass
class RobotStatus:
    """Current robot status"""
    connected: bool
    robot_id: Optional[str]
    robot_name: Optional[str]
    battery_level: int
    is_moving: bool
    last_command: Optional[str]
    last_error: Optional[str]


class RobotServiceInterface(ABC):
    """Abstract interface for robot control"""

    @abstractmethod
    async def connect(self, robot_name: Optional[str] = None, timeout: int = 30) -> bool:
        """Connect to robot via Bluetooth"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from robot"""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if robot is connected"""
        pass

    @abstractmethod
    async def get_status(self) -> RobotStatus:
        """Get current robot status"""
        pass

    # Movement commands
    @abstractmethod
    async def move_forward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Move robot forward"""
        pass

    @abstractmethod
    async def move_backward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Move robot backward"""
        pass

    @abstractmethod
    async def turn(self, degrees: float, speed_deg_s: float = 90.0) -> Dict[str, Any]:
        """Turn robot (positive = clockwise)"""
        pass

    @abstractmethod
    async def stop(self):
        """Emergency stop"""
        pass

    # Sensors
    @abstractmethod
    async def get_sensor_data(self) -> SensorData:
        """Get all sensor readings"""
        pass

    @abstractmethod
    async def get_distance_sensors(self) -> Dict[str, float]:
        """Get distance sensor readings in cm"""
        pass

    # Lights
    @abstractmethod
    async def set_lights(self, color: str, location: str = "all") -> Dict[str, Any]:
        """Set LED lights"""
        pass

    @abstractmethod
    async def set_lights_rgb(self, r: int, g: int, b: int, location: str = "all") -> Dict[str, Any]:
        """Set LED lights with RGB values"""
        pass

    # Head
    @abstractmethod
    async def move_head(self, pan_degrees: float, tilt_degrees: float, duration: float = 1.0) -> Dict[str, Any]:
        """Move robot head"""
        pass

    # Sound
    @abstractmethod
    async def play_tone(self, frequency_hz: int, duration_ms: int) -> Dict[str, Any]:
        """Play a tone"""
        pass

    @abstractmethod
    async def play_sound_file(self, file_path: str) -> Dict[str, Any]:
        """Play an audio file"""
        pass


class WonderPyRobotService(RobotServiceInterface):
    """Real WonderPy robot implementation"""

    def __init__(self):
        self._robot = None
        self._connected = False
        self._robot_id = None
        self._robot_name = None
        self._last_command = None
        self._last_error = None
        self._sensor_data: Optional[SensorData] = None

    async def connect(self, robot_name: Optional[str] = None, timeout: int = 30) -> bool:
        """Connect to Dash robot via Bluetooth"""
        try:
            import WonderPy.core.wwMain as wwMain
            from WonderPy.components.wwRobotConstants import WWRobotConstants

            logger.info(f"Scanning for robots (timeout: {timeout}s)...")

            # Scan for robots
            robots = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: wwMain.discover(timeout=timeout)
            )

            if not robots:
                logger.error("No robots found")
                self._last_error = "No robots found during scan"
                return False

            # Filter by name if specified
            if robot_name:
                robots = [r for r in robots if r.name == robot_name]
                if not robots:
                    logger.error(f"Robot '{robot_name}' not found")
                    self._last_error = f"Robot '{robot_name}' not found"
                    return False

            # Connect to first available robot
            self._robot = robots[0]
            self._robot_id = self._robot.serial_number
            self._robot_name = self._robot.name

            logger.info(f"Connected to {self._robot_name} (ID: {self._robot_id})")

            # Start sensor monitoring
            await self._start_sensor_monitoring()

            self._connected = True
            return True

        except ImportError:
            logger.error("WonderPy not installed. Install with: pip install WonderPy")
            self._last_error = "WonderPy not installed"
            return False
        except Exception as e:
            logger.error(f"Failed to connect to robot: {e}")
            self._last_error = str(e)
            return False

    async def _start_sensor_monitoring(self):
        """Start background sensor monitoring"""
        # TODO: Implement sensor data streaming
        # This would use WonderPy's sensor delegates to continuously update self._sensor_data
        pass

    async def disconnect(self):
        """Disconnect from robot"""
        if self._robot:
            try:
                self._robot.disconnect()
                logger.info(f"Disconnected from {self._robot_name}")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")

        self._robot = None
        self._connected = False
        self._robot_id = None
        self._robot_name = None

    async def is_connected(self) -> bool:
        """Check if robot is connected"""
        return self._connected and self._robot is not None

    async def get_status(self) -> RobotStatus:
        """Get current robot status"""
        battery = 0
        if self._connected and self._sensor_data:
            battery = self._sensor_data.battery_level

        return RobotStatus(
            connected=self._connected,
            robot_id=self._robot_id,
            robot_name=self._robot_name,
            battery_level=battery,
            is_moving=False,  # TODO: Track movement state
            last_command=self._last_command,
            last_error=self._last_error,
        )

    async def move_forward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Move robot forward"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"move_forward({distance_cm}cm, {speed_cm_s}cm/s)"

            # Execute WonderPy command
            self._robot.commands.body.do_forward(
                distance_cm=distance_cm,
                speed_cm_s=speed_cm_s
            )

            # Wait for completion (approximate)
            duration = distance_cm / speed_cm_s
            await asyncio.sleep(duration)

            logger.info(f"Moved forward {distance_cm}cm at {speed_cm_s}cm/s")

            return {
                "success": True,
                "distance_cm": distance_cm,
                "speed_cm_s": speed_cm_s,
                "duration_s": duration,
            }

        except Exception as e:
            logger.error(f"Failed to move forward: {e}")
            self._last_error = str(e)
            return {
                "success": False,
                "error": str(e),
            }

    async def move_backward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Move robot backward"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"move_backward({distance_cm}cm, {speed_cm_s}cm/s)"

            # WonderPy uses negative distance for backward
            self._robot.commands.body.do_forward(
                distance_cm=-distance_cm,
                speed_cm_s=speed_cm_s
            )

            duration = distance_cm / speed_cm_s
            await asyncio.sleep(duration)

            logger.info(f"Moved backward {distance_cm}cm at {speed_cm_s}cm/s")

            return {
                "success": True,
                "distance_cm": distance_cm,
                "speed_cm_s": speed_cm_s,
                "duration_s": duration,
            }

        except Exception as e:
            logger.error(f"Failed to move backward: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    async def turn(self, degrees: float, speed_deg_s: float = 90.0) -> Dict[str, Any]:
        """Turn robot (positive = clockwise, negative = counter-clockwise)"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"turn({degrees}°, {speed_deg_s}°/s)"

            is_clockwise = degrees > 0
            degrees_abs = abs(degrees)

            self._robot.commands.body.do_turn(
                degrees=degrees_abs,
                speed_deg_s=speed_deg_s,
                is_clockwise=is_clockwise
            )

            duration = degrees_abs / speed_deg_s
            await asyncio.sleep(duration)

            direction = "clockwise" if is_clockwise else "counter-clockwise"
            logger.info(f"Turned {degrees_abs}° {direction}")

            return {
                "success": True,
                "degrees": degrees,
                "speed_deg_s": speed_deg_s,
                "duration_s": duration,
                "direction": direction,
            }

        except Exception as e:
            logger.error(f"Failed to turn: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    async def stop(self):
        """Emergency stop"""
        if not self._connected:
            return

        try:
            self._robot.commands.body.stop()
            logger.warning("EMERGENCY STOP executed")
            self._last_command = "STOP"
        except Exception as e:
            logger.error(f"Failed to stop: {e}")

    async def get_sensor_data(self) -> SensorData:
        """Get all sensor readings"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        # TODO: Implement actual sensor reading from WonderPy
        # For now, return cached data or defaults
        if self._sensor_data:
            return self._sensor_data

        return SensorData(
            timestamp=datetime.now(),
            distance_front_left=100.0,
            distance_front_right=100.0,
            distance_rear=100.0,
            accel_x=0.0, accel_y=0.0, accel_z=9.8,
            gyro_x=0.0, gyro_y=0.0, gyro_z=0.0,
            pose_x=0.0, pose_y=0.0, pose_theta=0.0,
            battery_level=85,
            button_1_pressed=False,
            button_2_pressed=False,
            button_3_pressed=False,
        )

    async def get_distance_sensors(self) -> Dict[str, float]:
        """Get distance sensor readings in cm"""
        sensor_data = await self.get_sensor_data()

        return {
            "front_left_cm": sensor_data.distance_front_left,
            "front_right_cm": sensor_data.distance_front_right,
            "rear_cm": sensor_data.distance_rear,
            "front_cm": min(sensor_data.distance_front_left, sensor_data.distance_front_right),
        }

    async def set_lights(self, color: str, location: str = "all") -> Dict[str, Any]:
        """Set LED lights"""
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
            "orange": (255, 165, 0),
            "pink": (255, 192, 203),
            "off": (0, 0, 0),
        }

        if color not in color_map:
            raise ValueError(f"Unknown color: {color}. Available: {list(color_map.keys())}")

        r, g, b = color_map[color]
        return await self.set_lights_rgb(r, g, b, location)

    async def set_lights_rgb(self, r: int, g: int, b: int, location: str = "all") -> Dict[str, Any]:
        """Set LED lights with RGB values"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"set_lights_rgb({r}, {g}, {b}, {location})"

            if location == "all":
                self._robot.commands.RGB.set_all(r, g, b)
            elif location == "left_ear":
                self._robot.commands.RGB.set_ear_left(r, g, b)
            elif location == "right_ear":
                self._robot.commands.RGB.set_ear_right(r, g, b)
            elif location == "chest":
                self._robot.commands.RGB.set_chest(r, g, b)
            else:
                raise ValueError(f"Unknown location: {location}")

            logger.info(f"Set {location} lights to RGB({r}, {g}, {b})")

            return {
                "success": True,
                "r": r, "g": g, "b": b,
                "location": location,
            }

        except Exception as e:
            logger.error(f"Failed to set lights: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    async def move_head(self, pan_degrees: float, tilt_degrees: float, duration: float = 1.0) -> Dict[str, Any]:
        """Move robot head"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"move_head(pan={pan_degrees}°, tilt={tilt_degrees}°)"

            self._robot.commands.head.do_move(
                pan=pan_degrees,
                tilt=tilt_degrees,
                duration=duration
            )

            await asyncio.sleep(duration)

            logger.info(f"Moved head to pan={pan_degrees}°, tilt={tilt_degrees}°")

            return {
                "success": True,
                "pan_degrees": pan_degrees,
                "tilt_degrees": tilt_degrees,
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"Failed to move head: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    async def play_tone(self, frequency_hz: int, duration_ms: int) -> Dict[str, Any]:
        """Play a tone"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"play_tone({frequency_hz}Hz, {duration_ms}ms)"

            self._robot.commands.media.play_tone(frequency_hz, duration_ms)

            await asyncio.sleep(duration_ms / 1000.0)

            logger.info(f"Played tone: {frequency_hz}Hz for {duration_ms}ms")

            return {
                "success": True,
                "frequency_hz": frequency_hz,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Failed to play tone: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}

    async def play_sound_file(self, file_path: str) -> Dict[str, Any]:
        """Play an audio file"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        try:
            self._last_command = f"play_sound_file({file_path})"

            # TODO: Implement audio file playback via WonderPy
            # This may require converting audio to the correct format

            logger.info(f"Playing sound file: {file_path}")

            return {
                "success": True,
                "file_path": file_path,
            }

        except Exception as e:
            logger.error(f"Failed to play sound file: {e}")
            self._last_error = str(e)
            return {"success": False, "error": str(e)}


class MockRobotService(RobotServiceInterface):
    """Mock robot for testing without hardware"""

    def __init__(self):
        self._connected = False
        self._battery_level = 85
        self._position = {"x": 0.0, "y": 0.0, "theta": 0.0}
        self._head_position = {"pan": 0.0, "tilt": 0.0}
        self._lights = {"r": 0, "g": 0, "b": 0}
        self._last_command = None
        self._last_error = None

        logger.info("MockRobotService initialized (for testing)")

    async def connect(self, robot_name: Optional[str] = None, timeout: int = 30) -> bool:
        """Simulate connection"""
        logger.info(f"Mock: Connecting to robot (simulated)...")
        await asyncio.sleep(1.0)  # Simulate connection delay
        self._connected = True
        logger.info("Mock: Connected successfully")
        return True

    async def disconnect(self):
        """Simulate disconnection"""
        logger.info("Mock: Disconnecting...")
        self._connected = False

    async def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected

    async def get_status(self) -> RobotStatus:
        """Get mock status"""
        return RobotStatus(
            connected=self._connected,
            robot_id="MOCK-12345",
            robot_name="Dash (Mock)",
            battery_level=self._battery_level,
            is_moving=False,
            last_command=self._last_command,
            last_error=self._last_error,
        )

    async def move_forward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Simulate forward movement"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        self._last_command = f"move_forward({distance_cm}cm)"
        logger.info(f"Mock: Moving forward {distance_cm}cm at {speed_cm_s}cm/s")

        # Update simulated position
        import math
        theta_rad = math.radians(self._position["theta"])
        self._position["x"] += distance_cm * math.cos(theta_rad)
        self._position["y"] += distance_cm * math.sin(theta_rad)

        duration = distance_cm / speed_cm_s
        await asyncio.sleep(0.5)  # Simulate brief movement

        return {"success": True, "distance_cm": distance_cm, "duration_s": duration}

    async def move_backward(self, distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
        """Simulate backward movement"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        self._last_command = f"move_backward({distance_cm}cm)"
        logger.info(f"Mock: Moving backward {distance_cm}cm")

        import math
        theta_rad = math.radians(self._position["theta"])
        self._position["x"] -= distance_cm * math.cos(theta_rad)
        self._position["y"] -= distance_cm * math.sin(theta_rad)

        duration = distance_cm / speed_cm_s
        await asyncio.sleep(0.5)

        return {"success": True, "distance_cm": distance_cm, "duration_s": duration}

    async def turn(self, degrees: float, speed_deg_s: float = 90.0) -> Dict[str, Any]:
        """Simulate turning"""
        if not self._connected:
            raise RuntimeError("Robot not connected")

        self._last_command = f"turn({degrees}°)"
        logger.info(f"Mock: Turning {degrees}°")

        self._position["theta"] = (self._position["theta"] + degrees) % 360

        direction = "clockwise" if degrees > 0 else "counter-clockwise"
        duration = abs(degrees) / speed_deg_s
        await asyncio.sleep(0.5)

        return {"success": True, "degrees": degrees, "direction": direction, "duration_s": duration}

    async def stop(self):
        """Simulate stop"""
        logger.warning("Mock: EMERGENCY STOP")
        self._last_command = "STOP"

    async def get_sensor_data(self) -> SensorData:
        """Return mock sensor data"""
        return SensorData(
            timestamp=datetime.now(),
            distance_front_left=50.0,
            distance_front_right=50.0,
            distance_rear=100.0,
            accel_x=0.0, accel_y=0.0, accel_z=9.8,
            gyro_x=0.0, gyro_y=0.0, gyro_z=0.0,
            pose_x=self._position["x"],
            pose_y=self._position["y"],
            pose_theta=self._position["theta"],
            battery_level=self._battery_level,
            button_1_pressed=False,
            button_2_pressed=False,
            button_3_pressed=False,
        )

    async def get_distance_sensors(self) -> Dict[str, float]:
        """Return mock distance sensors"""
        return {
            "front_left_cm": 50.0,
            "front_right_cm": 50.0,
            "rear_cm": 100.0,
            "front_cm": 50.0,
        }

    async def set_lights(self, color: str, location: str = "all") -> Dict[str, Any]:
        """Simulate setting lights"""
        self._last_command = f"set_lights({color}, {location})"
        logger.info(f"Mock: Setting {location} lights to {color}")
        return {"success": True, "color": color, "location": location}

    async def set_lights_rgb(self, r: int, g: int, b: int, location: str = "all") -> Dict[str, Any]:
        """Simulate setting lights RGB"""
        self._last_command = f"set_lights_rgb({r}, {g}, {b})"
        self._lights = {"r": r, "g": g, "b": b}
        logger.info(f"Mock: Setting {location} lights to RGB({r}, {g}, {b})")
        return {"success": True, "r": r, "g": g, "b": b, "location": location}

    async def move_head(self, pan_degrees: float, tilt_degrees: float, duration: float = 1.0) -> Dict[str, Any]:
        """Simulate head movement"""
        self._last_command = f"move_head(pan={pan_degrees}, tilt={tilt_degrees})"
        self._head_position = {"pan": pan_degrees, "tilt": tilt_degrees}
        logger.info(f"Mock: Moving head to pan={pan_degrees}°, tilt={tilt_degrees}°")
        await asyncio.sleep(0.3)
        return {"success": True, "pan_degrees": pan_degrees, "tilt_degrees": tilt_degrees}

    async def play_tone(self, frequency_hz: int, duration_ms: int) -> Dict[str, Any]:
        """Simulate playing tone"""
        self._last_command = f"play_tone({frequency_hz}Hz)"
        logger.info(f"Mock: Playing tone {frequency_hz}Hz for {duration_ms}ms")
        await asyncio.sleep(duration_ms / 1000.0)
        return {"success": True, "frequency_hz": frequency_hz, "duration_ms": duration_ms}

    async def play_sound_file(self, file_path: str) -> Dict[str, Any]:
        """Simulate playing sound file"""
        self._last_command = f"play_sound_file({file_path})"
        logger.info(f"Mock: Playing sound file: {file_path}")
        return {"success": True, "file_path": file_path}


# Factory function to create appropriate robot service
def create_robot_service(use_mock: bool = False) -> RobotServiceInterface:
    """
    Create robot service instance

    Args:
        use_mock: If True, return MockRobotService. If False, return WonderPyRobotService.
    """
    if use_mock:
        return MockRobotService()
    else:
        return WonderPyRobotService()
