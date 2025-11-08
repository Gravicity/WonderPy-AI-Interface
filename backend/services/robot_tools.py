"""
Robot Control Tools for Claude Agent
Defines tools that the AI agent can use to control the robot
"""

from typing import Dict, Any, Callable, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Tool definition for Claude agent"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    function: Callable


class RobotTools:
    """
    Collection of robot control tools for Claude agent

    Each tool follows the pattern:
    - Validate inputs
    - Check safety
    - Execute command
    - Return structured result
    """

    def __init__(self, robot_service, safety_validator, voice_service=None):
        """
        Initialize robot tools

        Args:
            robot_service: RobotServiceInterface instance
            safety_validator: SafetyValidator instance
            voice_service: Optional VoiceService for TTS
        """
        self.robot = robot_service
        self.safety = safety_validator
        self.voice = voice_service

    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all available tools for the agent"""
        return [
            # Movement tools
            self.move_forward_tool(),
            self.move_backward_tool(),
            self.turn_tool(),
            self.stop_tool(),

            # Sensor tools
            self.check_sensors_tool(),
            self.get_battery_tool(),

            # Lights
            self.set_lights_tool(),

            # Head
            self.move_head_tool(),

            # Sound
            self.play_tone_tool(),
            self.speak_tool(),
        ]

    # ==================== MOVEMENT TOOLS ====================

    def move_forward_tool(self) -> ToolDefinition:
        """Tool for moving robot forward"""
        async def move_forward(distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
            """
            Move the robot forward by a specified distance

            Args:
                distance_cm: Distance to move in centimeters (1 foot = 30.48 cm)
                speed_cm_s: Speed in cm/s (default 20, max 50)

            Returns:
                Tool result with success status and details
            """
            logger.info(f"🤖 Tool: move_forward({distance_cm}cm, {speed_cm_s}cm/s)")

            # Safety check
            safety_result = await self.safety.validate_movement("forward", distance_cm, speed_cm_s)
            if not safety_result.safe:
                logger.warning(f"❌ Safety check failed: {safety_result.reason}")
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Cannot move forward - {safety_result.reason}\n\nSuggested action: {safety_result.suggested_action}"
                    }],
                    "is_error": True,
                }

            # Execute movement
            try:
                result = await self.robot.move_forward(distance_cm, speed_cm_s)

                if result.get("success"):
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"✅ Moved forward {distance_cm}cm at {speed_cm_s}cm/s (took {result.get('duration_s', 0):.1f}s)"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Movement failed: {result.get('error', 'Unknown error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                logger.error(f"Error executing move_forward: {e}")
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"❌ Error: {str(e)}"
                    }],
                    "is_error": True,
                }

        return ToolDefinition(
            name="move_forward",
            description="Move the Dash robot forward by a specified distance in centimeters. Always check distance sensors first to avoid obstacles. Convert feet to cm (1 foot = 30.48 cm).",
            input_schema={
                "type": "object",
                "properties": {
                    "distance_cm": {
                        "type": "number",
                        "description": "Distance to move in centimeters (1 foot = 30.48 cm)",
                        "minimum": 1,
                        "maximum": 500,
                    },
                    "speed_cm_s": {
                        "type": "number",
                        "description": "Speed in cm/s (default 20, max 50 for safety)",
                        "minimum": 5,
                        "maximum": 50,
                        "default": 20,
                    },
                },
                "required": ["distance_cm"],
            },
            function=move_forward
        )

    def move_backward_tool(self) -> ToolDefinition:
        """Tool for moving robot backward"""
        async def move_backward(distance_cm: float, speed_cm_s: float = 20.0) -> Dict[str, Any]:
            """Move the robot backward"""
            logger.info(f"🤖 Tool: move_backward({distance_cm}cm, {speed_cm_s}cm/s)")

            # Safety check
            safety_result = await self.safety.validate_movement("backward", distance_cm, speed_cm_s)
            if not safety_result.safe:
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Cannot move backward - {safety_result.reason}"
                    }],
                    "is_error": True,
                }

            try:
                result = await self.robot.move_backward(distance_cm, speed_cm_s)

                if result.get("success"):
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"✅ Moved backward {distance_cm}cm at {speed_cm_s}cm/s"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Movement failed: {result.get('error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                logger.error(f"Error executing move_backward: {e}")
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="move_backward",
            description="Move the Dash robot backward by a specified distance in centimeters.",
            input_schema={
                "type": "object",
                "properties": {
                    "distance_cm": {
                        "type": "number",
                        "description": "Distance to move in centimeters",
                        "minimum": 1,
                        "maximum": 500,
                    },
                    "speed_cm_s": {
                        "type": "number",
                        "description": "Speed in cm/s",
                        "minimum": 5,
                        "maximum": 50,
                        "default": 20,
                    },
                },
                "required": ["distance_cm"],
            },
            function=move_backward
        )

    def turn_tool(self) -> ToolDefinition:
        """Tool for turning robot"""
        async def turn(degrees: float, speed_deg_s: float = 90.0) -> Dict[str, Any]:
            """Turn the robot"""
            logger.info(f"🤖 Tool: turn({degrees}°, {speed_deg_s}°/s)")

            # Safety check
            safety_result = await self.safety.validate_turn(degrees, speed_deg_s)
            if not safety_result.safe:
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Cannot turn - {safety_result.reason}"
                    }],
                    "is_error": True,
                }

            try:
                result = await self.robot.turn(degrees, speed_deg_s)

                if result.get("success"):
                    direction = result.get("direction", "")
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"✅ Turned {abs(degrees)}° {direction}"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Turn failed: {result.get('error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                logger.error(f"Error executing turn: {e}")
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="turn",
            description="Turn the robot by specified degrees. Positive degrees = clockwise, negative = counter-clockwise. Examples: 90 (quarter turn right), -90 (quarter turn left), 180 (turn around).",
            input_schema={
                "type": "object",
                "properties": {
                    "degrees": {
                        "type": "number",
                        "description": "Degrees to turn. Positive = clockwise, negative = counter-clockwise.",
                        "minimum": -720,
                        "maximum": 720,
                    },
                    "speed_deg_s": {
                        "type": "number",
                        "description": "Turn speed in degrees/second",
                        "default": 90,
                        "minimum": 30,
                        "maximum": 180,
                    },
                },
                "required": ["degrees"],
            },
            function=turn
        )

    def stop_tool(self) -> ToolDefinition:
        """Tool for emergency stop"""
        async def stop() -> Dict[str, Any]:
            """Emergency stop the robot"""
            logger.warning("🤖 Tool: EMERGENCY STOP")

            try:
                await self.robot.stop()
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": "🛑 EMERGENCY STOP executed - robot stopped"
                    }],
                    "is_error": False,
                }
            except Exception as e:
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Stop failed: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="stop",
            description="EMERGENCY STOP - immediately halt all robot movement. Use if obstacle detected or user requests stop.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            function=stop
        )

    # ==================== SENSOR TOOLS ====================

    def check_sensors_tool(self) -> ToolDefinition:
        """Tool for checking distance sensors"""
        async def check_sensors() -> Dict[str, Any]:
            """Check distance sensors for obstacles"""
            logger.info("🤖 Tool: check_sensors")

            try:
                sensors = await self.robot.get_distance_sensors()

                front_left = sensors.get("front_left_cm", 0)
                front_right = sensors.get("front_right_cm", 0)
                rear = sensors.get("rear_cm", 0)
                front_min = min(front_left, front_right)

                # Determine status
                if front_min < 10:
                    status = "⚠️ OBSTACLE DETECTED - too close to proceed"
                elif front_min < 20:
                    status = "⚠️ Warning - obstacle nearby, proceed with caution"
                else:
                    status = "✅ Path clear"

                text = f"""Distance Sensors:
- Front Left: {front_left:.1f} cm
- Front Right: {front_right:.1f} cm
- Rear: {rear:.1f} cm

Status: {status}"""

                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": text}],
                    "is_error": False,
                }

            except Exception as e:
                logger.error(f"Error reading sensors: {e}")
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Sensor read failed: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="check_sensors",
            description="Get current distance sensor readings to detect obstacles. CRITICAL: Always call this before moving forward to ensure safety.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            function=check_sensors
        )

    def get_battery_tool(self) -> ToolDefinition:
        """Tool for checking battery level"""
        async def get_battery() -> Dict[str, Any]:
            """Get robot battery level"""
            logger.info("🤖 Tool: get_battery")

            try:
                status = await self.robot.get_status()
                battery = status.battery_level

                if battery < 15:
                    status_text = "🔴 CRITICAL - charge soon"
                elif battery < 30:
                    status_text = "🟡 LOW - consider charging"
                else:
                    status_text = "🟢 GOOD"

                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"Battery Level: {battery}% {status_text}"
                    }],
                    "is_error": False,
                }

            except Exception as e:
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Could not read battery: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="get_battery",
            description="Get the current battery level percentage of the robot.",
            input_schema={
                "type": "object",
                "properties": {},
            },
            function=get_battery
        )

    # ==================== LIGHT TOOLS ====================

    def set_lights_tool(self) -> ToolDefinition:
        """Tool for setting LED lights"""
        async def set_lights(color: str, location: str = "all") -> Dict[str, Any]:
            """Set robot LED lights"""
            logger.info(f"🤖 Tool: set_lights({color}, {location})")

            try:
                result = await self.robot.set_lights(color, location)

                if result.get("success"):
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"✅ Set {location} lights to {color}"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Failed to set lights: {result.get('error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="set_lights",
            description="Change the color of robot's LED lights. Use to express emotions or provide visual feedback.",
            input_schema={
                "type": "object",
                "properties": {
                    "color": {
                        "type": "string",
                        "enum": ["red", "green", "blue", "yellow", "purple", "cyan", "white", "orange", "pink", "off"],
                        "description": "Color preset to set",
                    },
                    "location": {
                        "type": "string",
                        "enum": ["all", "left_ear", "right_ear", "chest"],
                        "default": "all",
                        "description": "Which lights to change",
                    },
                },
                "required": ["color"],
            },
            function=set_lights
        )

    # ==================== HEAD TOOLS ====================

    def move_head_tool(self) -> ToolDefinition:
        """Tool for moving robot head"""
        async def move_head(pan_degrees: float, tilt_degrees: float) -> Dict[str, Any]:
            """Move robot head to look around"""
            logger.info(f"🤖 Tool: move_head(pan={pan_degrees}°, tilt={tilt_degrees}°)")

            # Safety check
            safety_result = await self.safety.validate_head_movement(pan_degrees, tilt_degrees)
            if not safety_result.safe:
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ Cannot move head - {safety_result.reason}"
                    }],
                    "is_error": True,
                }

            try:
                result = await self.robot.move_head(pan_degrees, tilt_degrees)

                if result.get("success"):
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"✅ Moved head to pan={pan_degrees}°, tilt={tilt_degrees}°"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Failed: {result.get('error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="move_head",
            description="Move the robot's head to look around. Pan moves left/right, tilt moves up/down.",
            input_schema={
                "type": "object",
                "properties": {
                    "pan_degrees": {
                        "type": "number",
                        "description": "Horizontal rotation (-120 to 120). Negative = left, positive = right, 0 = center.",
                        "minimum": -120,
                        "maximum": 120,
                    },
                    "tilt_degrees": {
                        "type": "number",
                        "description": "Vertical tilt (-10 to 22). Negative = down, positive = up, 0 = level.",
                        "minimum": -10,
                        "maximum": 22,
                    },
                },
                "required": ["pan_degrees", "tilt_degrees"],
            },
            function=move_head
        )

    # ==================== SOUND TOOLS ====================

    def play_tone_tool(self) -> ToolDefinition:
        """Tool for playing tones"""
        async def play_tone(frequency_hz: int, duration_ms: int = 200) -> Dict[str, Any]:
            """Play a tone using robot's speaker"""
            logger.info(f"🤖 Tool: play_tone({frequency_hz}Hz, {duration_ms}ms)")

            # Safety check
            safety_result = await self.safety.validate_sound(frequency_hz, duration_ms)
            if not safety_result.safe:
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"⚠️ {safety_result.reason}"
                    }],
                    "is_error": True,
                }

            try:
                result = await self.robot.play_tone(frequency_hz, duration_ms)

                if result.get("success"):
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"🔊 Played {frequency_hz}Hz tone for {duration_ms}ms"
                        }],
                        "is_error": False,
                    }
                else:
                    return {
                        "type": "tool_result",
                        "content": [{
                            "type": "text",
                            "text": f"❌ Failed: {result.get('error')}"
                        }],
                        "is_error": True,
                    }

            except Exception as e:
                return {
                    "type": "tool_result",
                    "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                    "is_error": True,
                }

        return ToolDefinition(
            name="play_tone",
            description="Play a beep/tone using the robot's speaker. Use for sound effects or feedback.",
            input_schema={
                "type": "object",
                "properties": {
                    "frequency_hz": {
                        "type": "integer",
                        "description": "Frequency in Hz (200-2000 recommended for comfort)",
                        "minimum": 200,
                        "maximum": 2000,
                    },
                    "duration_ms": {
                        "type": "integer",
                        "description": "Duration in milliseconds",
                        "default": 200,
                        "minimum": 50,
                        "maximum": 5000,
                    },
                },
                "required": ["frequency_hz"],
            },
            function=play_tone
        )

    def speak_tool(self) -> ToolDefinition:
        """Tool for speaking text via TTS"""
        async def speak(text: str) -> Dict[str, Any]:
            """Speak text using TTS (Deepgram Aura)"""
            logger.info(f"🤖 Tool: speak('{text[:50]}...')")

            if self.voice is None:
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": "⚠️ Voice service not available (TTS not configured)"
                    }],
                    "is_error": True,
                }

            try:
                # Use voice service to speak
                await self.voice.speak(text)

                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"🔊 Spoke: \"{text}\""
                    }],
                    "is_error": False,
                }

            except Exception as e:
                logger.error(f"Error in speak tool: {e}")
                return {
                    "type": "tool_result",
                    "content": [{
                        "type": "text",
                        "text": f"❌ Speech failed: {str(e)}"
                    }],
                    "is_error": True,
                }

        return ToolDefinition(
            name="speak",
            description="Speak text out loud using the robot's speaker via text-to-speech. Use this to respond to the user verbally.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to speak out loud",
                        "maxLength": 500,
                    },
                },
                "required": ["text"],
            },
            function=speak
        )
