"""
Safety Validation Layer
Multi-tier safety checks before executing robot commands
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SafetyResult:
    """Result of safety validation"""
    safe: bool
    reason: Optional[str] = None
    severity: str = "info"  # info, warning, critical
    suggested_action: Optional[str] = None


class SafetyValidator:
    """
    Multi-layer safety validation for robot commands

    Safety Tiers:
    1. Hardware limits (speed, distance, angles)
    2. Sensor checks (obstacle detection)
    3. Battery checks
    4. Environmental checks
    """

    # Safety thresholds
    MAX_DISTANCE_CM = 500  # Maximum single movement distance
    MAX_SPEED_CM_S = 50  # Maximum movement speed
    MAX_TURN_SPEED_DEG_S = 180  # Maximum turn speed
    MIN_BATTERY_PERCENT = 15  # Minimum battery for movement
    OBSTACLE_THRESHOLD_CM = 10  # Minimum safe distance to obstacle
    WARNING_THRESHOLD_CM = 20  # Warning distance to obstacle

    def __init__(self, robot_service):
        """
        Initialize safety validator

        Args:
            robot_service: RobotServiceInterface instance for sensor access
        """
        self.robot_service = robot_service
        self._safety_enabled = True
        self._strict_mode = True  # If True, warnings become errors

    def enable_safety(self, enabled: bool = True):
        """Enable or disable safety checks (use with caution!)"""
        self._safety_enabled = enabled
        if not enabled:
            logger.warning("⚠️ SAFETY CHECKS DISABLED - Use extreme caution!")
        else:
            logger.info("✅ Safety checks enabled")

    def set_strict_mode(self, strict: bool = True):
        """
        Set strict mode

        Strict mode: Warnings are treated as errors (command blocked)
        Permissive mode: Warnings allow execution with logging
        """
        self._strict_mode = strict

    async def validate_movement(
        self,
        direction: str,
        distance_cm: float,
        speed_cm_s: float = 20.0
    ) -> SafetyResult:
        """
        Validate movement command safety

        Args:
            direction: "forward", "backward"
            distance_cm: Distance to travel in cm
            speed_cm_s: Speed in cm/s

        Returns:
            SafetyResult indicating if movement is safe
        """
        if not self._safety_enabled:
            return SafetyResult(safe=True, reason="Safety checks disabled")

        # 1. Hardware limit checks
        if distance_cm > self.MAX_DISTANCE_CM:
            return SafetyResult(
                safe=False,
                reason=f"Distance {distance_cm}cm exceeds safety limit ({self.MAX_DISTANCE_CM}cm)",
                severity="critical",
                suggested_action=f"Reduce distance to {self.MAX_DISTANCE_CM}cm or less"
            )

        if speed_cm_s > self.MAX_SPEED_CM_S:
            return SafetyResult(
                safe=False,
                reason=f"Speed {speed_cm_s}cm/s exceeds safety limit ({self.MAX_SPEED_CM_S}cm/s)",
                severity="critical",
                suggested_action=f"Reduce speed to {self.MAX_SPEED_CM_S}cm/s or less"
            )

        if distance_cm <= 0:
            return SafetyResult(
                safe=False,
                reason="Distance must be positive",
                severity="critical"
            )

        # 2. Battery check
        try:
            status = await self.robot_service.get_status()
            if status.battery_level < self.MIN_BATTERY_PERCENT:
                return SafetyResult(
                    safe=False,
                    reason=f"Battery too low ({status.battery_level}%) for movement",
                    severity="critical",
                    suggested_action="Charge the robot before attempting movement"
                )
        except Exception as e:
            logger.warning(f"Could not check battery level: {e}")

        # 3. Sensor checks (obstacle detection)
        if direction == "forward":
            try:
                sensors = await self.robot_service.get_distance_sensors()
                front_distance = sensors.get("front_cm", 100.0)

                # Critical: Too close to obstacle
                if front_distance < self.OBSTACLE_THRESHOLD_CM:
                    return SafetyResult(
                        safe=False,
                        reason=f"Obstacle detected {front_distance:.1f}cm ahead (minimum: {self.OBSTACLE_THRESHOLD_CM}cm)",
                        severity="critical",
                        suggested_action="Turn to avoid obstacle or move backward"
                    )

                # Warning: Getting close to obstacle
                if front_distance < self.WARNING_THRESHOLD_CM:
                    if self._strict_mode:
                        return SafetyResult(
                            safe=False,
                            reason=f"Obstacle detected {front_distance:.1f}cm ahead (warning threshold: {self.WARNING_THRESHOLD_CM}cm)",
                            severity="warning",
                            suggested_action="Proceed with caution or turn to avoid"
                        )
                    else:
                        logger.warning(f"⚠️ Obstacle at {front_distance:.1f}cm - proceeding with caution")

            except Exception as e:
                logger.error(f"Could not read sensors: {e}")
                # In strict mode, sensor failure blocks movement
                if self._strict_mode:
                    return SafetyResult(
                        safe=False,
                        reason=f"Cannot verify safety - sensor read failed: {e}",
                        severity="critical"
                    )

        # 4. Check if connected
        try:
            if not await self.robot_service.is_connected():
                return SafetyResult(
                    safe=False,
                    reason="Robot not connected",
                    severity="critical",
                    suggested_action="Connect to robot first"
                )
        except Exception as e:
            logger.error(f"Could not check connection status: {e}")

        # All checks passed
        return SafetyResult(
            safe=True,
            reason="All safety checks passed",
            severity="info"
        )

    async def validate_turn(
        self,
        degrees: float,
        speed_deg_s: float = 90.0
    ) -> SafetyResult:
        """
        Validate turn command safety

        Args:
            degrees: Degrees to turn
            speed_deg_s: Turn speed in degrees/s

        Returns:
            SafetyResult indicating if turn is safe
        """
        if not self._safety_enabled:
            return SafetyResult(safe=True, reason="Safety checks disabled")

        # 1. Hardware limit checks
        if abs(degrees) > 720:  # More than 2 full rotations
            return SafetyResult(
                safe=False,
                reason=f"Turn angle {degrees}° exceeds reasonable limit (720°)",
                severity="warning",
                suggested_action="Break large turns into smaller segments"
            )

        if speed_deg_s > self.MAX_TURN_SPEED_DEG_S:
            return SafetyResult(
                safe=False,
                reason=f"Turn speed {speed_deg_s}°/s exceeds safety limit ({self.MAX_TURN_SPEED_DEG_S}°/s)",
                severity="critical",
                suggested_action=f"Reduce turn speed to {self.MAX_TURN_SPEED_DEG_S}°/s or less"
            )

        # 2. Battery check
        try:
            status = await self.robot_service.get_status()
            if status.battery_level < self.MIN_BATTERY_PERCENT:
                return SafetyResult(
                    safe=False,
                    reason=f"Battery too low ({status.battery_level}%) for turning",
                    severity="critical"
                )
        except Exception as e:
            logger.warning(f"Could not check battery level: {e}")

        # 3. Connection check
        try:
            if not await self.robot_service.is_connected():
                return SafetyResult(
                    safe=False,
                    reason="Robot not connected",
                    severity="critical"
                )
        except Exception as e:
            logger.error(f"Could not check connection status: {e}")

        return SafetyResult(safe=True, reason="All safety checks passed")

    async def validate_head_movement(
        self,
        pan_degrees: float,
        tilt_degrees: float
    ) -> SafetyResult:
        """
        Validate head movement safety

        Args:
            pan_degrees: Horizontal rotation (-120 to 120)
            tilt_degrees: Vertical tilt (-10 to 22)

        Returns:
            SafetyResult indicating if movement is safe
        """
        if not self._safety_enabled:
            return SafetyResult(safe=True, reason="Safety checks disabled")

        # Hardware limits for Dash head
        PAN_MIN, PAN_MAX = -120, 120
        TILT_MIN, TILT_MAX = -10, 22

        if not (PAN_MIN <= pan_degrees <= PAN_MAX):
            return SafetyResult(
                safe=False,
                reason=f"Pan angle {pan_degrees}° out of range ({PAN_MIN}° to {PAN_MAX}°)",
                severity="critical",
                suggested_action=f"Use pan angle between {PAN_MIN}° and {PAN_MAX}°"
            )

        if not (TILT_MIN <= tilt_degrees <= TILT_MAX):
            return SafetyResult(
                safe=False,
                reason=f"Tilt angle {tilt_degrees}° out of range ({TILT_MIN}° to {TILT_MAX}°)",
                severity="critical",
                suggested_action=f"Use tilt angle between {TILT_MIN}° and {TILT_MAX}°"
            )

        return SafetyResult(safe=True, reason="Head movement within limits")

    async def validate_lights(
        self,
        r: int,
        g: int,
        b: int
    ) -> SafetyResult:
        """
        Validate light settings

        Args:
            r, g, b: RGB values (0-255)

        Returns:
            SafetyResult indicating if values are safe
        """
        if not self._safety_enabled:
            return SafetyResult(safe=True, reason="Safety checks disabled")

        if not all(0 <= val <= 255 for val in [r, g, b]):
            return SafetyResult(
                safe=False,
                reason=f"RGB values must be 0-255. Got: ({r}, {g}, {b})",
                severity="critical"
            )

        return SafetyResult(safe=True)

    async def validate_sound(
        self,
        frequency_hz: Optional[int] = None,
        duration_ms: Optional[int] = None
    ) -> SafetyResult:
        """
        Validate sound playback

        Args:
            frequency_hz: Tone frequency
            duration_ms: Tone duration

        Returns:
            SafetyResult indicating if sound is safe
        """
        if not self._safety_enabled:
            return SafetyResult(safe=True, reason="Safety checks disabled")

        if frequency_hz is not None:
            # Human hearing range: 20Hz - 20kHz
            # Comfortable range for beeps: 200Hz - 2kHz
            if not (200 <= frequency_hz <= 2000):
                return SafetyResult(
                    safe=False,
                    reason=f"Frequency {frequency_hz}Hz may be uncomfortable (recommended: 200-2000Hz)",
                    severity="warning",
                    suggested_action="Use frequency between 200Hz and 2000Hz"
                )

        if duration_ms is not None:
            if duration_ms > 5000:  # 5 seconds max
                return SafetyResult(
                    safe=False,
                    reason=f"Duration {duration_ms}ms too long (max: 5000ms)",
                    severity="warning",
                    suggested_action="Keep tones under 5 seconds"
                )

        return SafetyResult(safe=True)

    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety configuration"""
        return {
            "enabled": self._safety_enabled,
            "strict_mode": self._strict_mode,
            "thresholds": {
                "max_distance_cm": self.MAX_DISTANCE_CM,
                "max_speed_cm_s": self.MAX_SPEED_CM_S,
                "max_turn_speed_deg_s": self.MAX_TURN_SPEED_DEG_S,
                "min_battery_percent": self.MIN_BATTERY_PERCENT,
                "obstacle_threshold_cm": self.OBSTACLE_THRESHOLD_CM,
                "warning_threshold_cm": self.WARNING_THRESHOLD_CM,
            }
        }
