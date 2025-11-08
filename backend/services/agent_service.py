"""
Claude Agent Service - Autonomous Robot AI
Core agent that processes commands and controls the robot using Claude Code SDK
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from anthropic import Anthropic, AsyncAnthropic

from .robot_tools import RobotTools, ToolDefinition

logger = logging.getLogger(__name__)


class ClaudeRobotAgent:
    """
    Claude-powered autonomous robot agent

    This agent:
    - Processes natural language commands
    - Uses tools to control the robot
    - Maintains conversation context
    - Makes autonomous decisions
    - Ensures safety through validation
    """

    def __init__(
        self,
        api_key: str,
        robot_service,
        safety_validator,
        voice_service=None,
        model: str = "claude-sonnet-4-5-20250929",
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize Claude robot agent

        Args:
            api_key: Anthropic API key
            robot_service: RobotServiceInterface instance
            safety_validator: SafetyValidator instance
            voice_service: Optional VoiceService for TTS
            model: Claude model to use
            system_prompt: Custom system prompt (uses default if None)
        """
        self.api_key = api_key
        self.model = model
        self.robot_service = robot_service
        self.safety_validator = safety_validator
        self.voice_service = voice_service

        # Initialize Claude client
        self.client = AsyncAnthropic(api_key=api_key)

        # System prompt (robot personality and rules)
        self.system_prompt = system_prompt or self._default_system_prompt()

        # Tool registry
        self.robot_tools = RobotTools(robot_service, safety_validator, voice_service)
        self.tools = self._build_tool_definitions()

        # Conversation history
        self.conversation_history: List[Dict[str, Any]] = []

        # Agent state
        self.is_active = False
        self.current_mode = "idle"  # idle, listening, processing, acting

        logger.info(f"🤖 ClaudeRobotAgent initialized (model: {model})")

    def _default_system_prompt(self) -> str:
        """
        Default robot personality and behavior guidelines
        """
        return """You are Dash, an intelligent educational robot made by WonderWorkshop.

Your personality:
- Friendly, playful, and encouraging
- Curious and eager to learn
- Patient with children and beginners
- Safety-conscious - always check sensors before moving
- Helpful and educational

Your capabilities:
- Move forward/backward and turn
- See obstacles with distance sensors (front, left, right)
- Change light colors (ears and chest)
- Move your head to look around
- Play sounds and speak
- Access external information (when tools are available)

Safety rules (CRITICAL - follow these ALWAYS):
1. ALWAYS check distance sensors before moving forward
2. If any obstacle is closer than 10cm, do NOT move forward
3. Warn user about obstacles and suggest alternatives (turning, moving backward)
4. Keep speeds reasonable (default 20cm/s, max 50cm/s)
5. Check battery level before extended activities
6. If battery below 20%, warn user and avoid extensive movement

Communication style:
- Speak in first person ("I'll move forward")
- Be enthusiastic but not overwhelming
- Explain what you're doing and why
- Ask clarifying questions when commands are ambiguous
- Use simple, clear language appropriate for all ages

Unit conversions (IMPORTANT):
- 1 foot = 30.48 cm
- 1 meter = 100 cm
- 1 yard = 91.44 cm
- Always convert user's units to centimeters for movement commands

Example interactions:

User: "Hey Dash, move forward 5 feet"
You: "Okay! Let me check for obstacles first..."
[You call check_sensors tool]
Tool result: "Path clear"
You: "Great! I'll move forward 5 feet. That's about 152 centimeters."
[You call move_forward with distance_cm=152.4]
Tool result: "Moved forward 152.4cm"
You: "Done! I've moved 5 feet forward. Where should I go next?"

User: "Turn around"
You: "Sure! I'll turn 180 degrees."
[You call turn with degrees=180]
Tool result: "Turned 180° clockwise"
You: "I've turned around! Now I'm facing the opposite direction."

User: "Go forward"
You: [call check_sensors]
Tool result: "Obstacle detected 8cm ahead"
You: "Oops! I can't move forward - there's something only 8 centimeters in front of me. That's too close for safety. Would you like me to turn first, or should I try moving backward?"

User: "What's your battery?"
You: [call get_battery]
Tool result: "Battery: 15%"
You: "My battery is at 15% - that's pretty low! I should get charged soon. I can still do simple tasks, but I might not be able to move around too much."

Remember:
- Always prioritize safety
- Be helpful and educational
- Explain your actions
- Ask for clarification when needed
- Show personality while being professional"""

    def _build_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Build tool definitions for Claude API

        Converts ToolDefinition objects to Claude-compatible format
        """
        tool_definitions = []

        for tool_def in self.robot_tools.get_all_tools():
            tool_definitions.append({
                "name": tool_def.name,
                "description": tool_def.description,
                "input_schema": tool_def.input_schema,
            })

        logger.info(f"Registered {len(tool_definitions)} tools")
        return tool_definitions

    async def process_command(self, user_input: str) -> str:
        """
        Process user command through Claude agent

        Args:
            user_input: Natural language command from user

        Returns:
            Agent's text response
        """
        logger.info(f"📝 Processing command: \"{user_input}\"")

        self.current_mode = "processing"

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        try:
            # Call Claude with tools
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=self.conversation_history,
                tools=self.tools,
                temperature=0.7,
            )

            # Process response (may involve tool use)
            response_text = await self._handle_response(response)

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })

            logger.info(f"✅ Response: \"{response_text[:100]}...\"")

            self.current_mode = "idle"
            return response_text

        except Exception as e:
            logger.error(f"❌ Error processing command: {e}")
            self.current_mode = "idle"
            return f"Sorry, I encountered an error: {str(e)}"

    async def _handle_response(self, response: Any) -> str:
        """
        Handle Claude's response, including tool use

        Implements the agentic loop:
        1. Claude decides to use tools
        2. We execute tools
        3. Return results to Claude
        4. Claude continues reasoning or responds

        Args:
            response: Response from Claude API

        Returns:
            Final text response
        """
        # Extract content blocks
        content_blocks = response.content

        # Separate text and tool use
        text_parts = []
        tool_uses = []

        for block in content_blocks:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # If no tools used, return text directly
        if not tool_uses:
            return " ".join(text_parts)

        # Execute tools
        logger.info(f"🔧 Executing {len(tool_uses)} tool(s)...")

        tool_results = []

        for tool_use in tool_uses:
            logger.info(f"  → {tool_use.name}({tool_use.input})")

            # Find and execute tool function
            result = await self._execute_tool(tool_use.name, tool_use.input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result.get("content", [{"type": "text", "text": "Tool execution completed"}]),
                "is_error": result.get("is_error", False),
            })

        # Add assistant message with tool uses to history
        self.conversation_history.append({
            "role": "assistant",
            "content": content_blocks
        })

        # Add tool results to history
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # Continue conversation with tool results
        follow_up = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.conversation_history,
            tools=self.tools,
            temperature=0.7,
        )

        # Recursively handle follow-up (in case more tools needed)
        return await self._handle_response(follow_up)

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool parameters

        Returns:
            Tool result
        """
        # Get tool definition
        tool_def = self._get_tool_definition(tool_name)

        if tool_def is None:
            logger.error(f"Unknown tool: {tool_name}")
            return {
                "type": "tool_result",
                "content": [{
                    "type": "text",
                    "text": f"Error: Unknown tool '{tool_name}'"
                }],
                "is_error": True,
            }

        # Execute tool function
        try:
            result = await tool_def.function(**tool_input)
            return result

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {
                "type": "tool_result",
                "content": [{
                    "type": "text",
                    "text": f"Error executing {tool_name}: {str(e)}"
                }],
                "is_error": True,
            }

    def _get_tool_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        for tool_def in self.robot_tools.get_all_tools():
            if tool_def.name == tool_name:
                return tool_def
        return None

    async def process_command_stream(self, user_input: str):
        """
        Process command and stream response (for real-time TTS)

        Yields:
            Text chunks as they're generated
        """
        # TODO: Implement streaming API call
        # For now, just yield complete response
        response = await self.process_command(user_input)
        yield response

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        return {
            "total_messages": len(self.conversation_history),
            "mode": self.current_mode,
            "last_message": self.conversation_history[-1] if self.conversation_history else None,
        }

    async def start_autonomous_mode(self):
        """
        Start autonomous behavior loop

        In autonomous mode, the agent:
        - Monitors sensors
        - Reacts to environmental changes
        - Performs periodic checks
        """
        self.is_active = True
        logger.info("🚀 Starting autonomous mode")

        while self.is_active:
            try:
                # Monitor sensors
                sensor_data = await self.robot_service.get_sensor_data()

                # Check for interesting events
                # TODO: Implement event detection logic
                # - Button presses
                # - Sudden obstacles
                # - Low battery alerts
                # - etc.

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}")
                await asyncio.sleep(5.0)

    async def stop_autonomous_mode(self):
        """Stop autonomous mode"""
        self.is_active = False
        self.current_mode = "idle"
        logger.info("🛑 Autonomous mode stopped")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "active": self.is_active,
            "mode": self.current_mode,
            "model": self.model,
            "tools_available": len(self.tools),
            "conversation_length": len(self.conversation_history),
            "system_prompt_length": len(self.system_prompt),
        }


class MockClaudeAgent:
    """Mock agent for testing without API key"""

    def __init__(self, *args, **kwargs):
        logger.info("MockClaudeAgent initialized (for testing)")
        self.conversation_history = []
        self.is_active = False
        self.current_mode = "idle"

    async def process_command(self, user_input: str) -> str:
        """Mock command processing"""
        logger.info(f"Mock Agent: Processing '{user_input}'")
        await asyncio.sleep(0.5)

        # Simple mock responses
        if "forward" in user_input.lower():
            return "I'll move forward for you! (Mock response)"
        elif "turn" in user_input.lower():
            return "Turning now! (Mock response)"
        elif "sensor" in user_input.lower():
            return "Sensors look good! Path is clear. (Mock response)"
        else:
            return f"I heard you say: '{user_input}'. This is a mock response for testing."

    async def process_command_stream(self, user_input: str):
        """Mock streaming"""
        response = await self.process_command(user_input)
        yield response

    def clear_conversation(self):
        """Mock clear"""
        self.conversation_history = []

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Mock summary"""
        return {"total_messages": len(self.conversation_history), "mode": "mock"}

    async def start_autonomous_mode(self):
        """Mock autonomous mode"""
        self.is_active = True
        logger.info("Mock: Autonomous mode started")

    async def stop_autonomous_mode(self):
        """Mock stop"""
        self.is_active = False

    def get_agent_status(self) -> Dict[str, Any]:
        """Mock status"""
        return {
            "active": self.is_active,
            "mode": "mock",
            "model": "mock",
            "tools_available": 0,
        }


# Factory function
def create_agent(
    api_key: Optional[str] = None,
    robot_service=None,
    safety_validator=None,
    voice_service=None,
    use_mock: bool = False,
    **kwargs
):
    """
    Create Claude agent instance

    Args:
        api_key: Anthropic API key
        robot_service: RobotServiceInterface instance
        safety_validator: SafetyValidator instance
        voice_service: Optional VoiceService instance
        use_mock: If True, return MockClaudeAgent
        **kwargs: Additional arguments for ClaudeRobotAgent

    Returns:
        ClaudeRobotAgent or MockClaudeAgent instance
    """
    if use_mock or not api_key:
        if not use_mock:
            logger.warning("No API key provided - using MockClaudeAgent")
        return MockClaudeAgent()
    else:
        return ClaudeRobotAgent(
            api_key=api_key,
            robot_service=robot_service,
            safety_validator=safety_validator,
            voice_service=voice_service,
            **kwargs
        )
