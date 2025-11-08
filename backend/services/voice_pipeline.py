"""
Voice-to-Action Pipeline
Coordinates: Wake Word → STT → Claude Agent → Robot Action → TTS
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VoiceActionPipeline:
    """
    Complete voice interaction pipeline for autonomous robot

    Pipeline flow:
    1. Wake Word Detection (Porcupine) - "Hey Dash"
    2. Play acknowledgment sound
    3. Speech-to-Text (Deepgram) - capture user command
    4. Claude Agent - process command and execute tools
    5. Text-to-Speech (Deepgram) - speak response
    6. Return to listening for wake word

    This enables natural voice interactions:
    User: "Hey Dash, move forward 5 feet"
    Robot: [beep] "Okay! Let me check for obstacles first... All clear! I'll move forward 5 feet." [moves] "Done!"
    """

    def __init__(
        self,
        wake_word_detector,
        voice_service,
        agent,
        robot_service,
    ):
        """
        Initialize voice-to-action pipeline

        Args:
            wake_word_detector: WakeWordDetector instance
            voice_service: VoiceService instance
            agent: ClaudeRobotAgent instance
            robot_service: RobotServiceInterface instance
        """
        self.wake_word = wake_word_detector
        self.voice = voice_service
        self.agent = agent
        self.robot = robot_service

        self._is_running = False
        self._interaction_count = 0

        logger.info("🎙️ VoiceActionPipeline initialized")

    async def run_continuous_loop(self):
        """
        Run continuous voice interaction loop

        This is the main loop for autonomous voice control:
        - Always listening for wake word
        - Processes commands when detected
        - Returns to listening after each interaction
        """
        logger.info("🚀 Starting continuous voice interaction loop...")

        self._is_running = True

        while self._is_running:
            try:
                # 1. Listen for wake word
                logger.info("👂 Listening for wake word...")

                wake_detected = await self.wake_word.detect_once(timeout=60.0)

                if not wake_detected:
                    continue  # Timeout, try again

                # 2. Wake word detected - process interaction
                await self._process_interaction()

            except Exception as e:
                logger.error(f"Error in voice loop: {e}")
                await asyncio.sleep(2.0)  # Brief pause before retrying

        logger.info("🛑 Voice interaction loop stopped")

    async def _process_interaction(self):
        """
        Process a single voice interaction

        Steps:
        1. Play acknowledgment
        2. Capture voice command (STT)
        3. Process through agent
        4. Speak response (TTS)
        """
        self._interaction_count += 1
        interaction_id = self._interaction_count

        logger.info(f"\n{'=' * 60}")
        logger.info(f"🎙️ INTERACTION #{interaction_id} - {datetime.now().strftime('%H:%M:%S')}")
        logger.info(f"{'=' * 60}")

        try:
            # 1. Play acknowledgment sound
            logger.info("🔊 Playing acknowledgment...")
            await self.robot.play_tone(800, 100)  # Quick beep

            # 2. Capture voice command
            logger.info("👂 Listening for command...")

            # TODO: Implement actual microphone capture
            # For now, use a simple prompt
            command_text = await self._capture_voice_command(timeout=5.0)

            if not command_text or len(command_text.strip()) == 0:
                logger.warning("No command heard")
                await self.voice.speak("I didn't hear anything. Try again!")
                return

            logger.info(f"📝 Heard: \"{command_text}\"")

            # 3. Process through Claude agent
            logger.info("🤖 Processing with Claude agent...")
            response_text = await self.agent.process_command(command_text)

            logger.info(f"💬 Response: \"{response_text}\"")

            # 4. Speak response
            logger.info("🔊 Speaking response...")
            await self.voice.speak(response_text)

            logger.info(f"✅ Interaction #{interaction_id} complete")

        except Exception as e:
            logger.error(f"❌ Interaction #{interaction_id} failed: {e}")
            try:
                await self.voice.speak("Sorry, I encountered an error.")
            except:
                pass

        logger.info(f"{'=' * 60}\n")

    async def _capture_voice_command(self, timeout: float = 5.0) -> str:
        """
        Capture voice command using STT

        Args:
            timeout: Maximum time to listen

        Returns:
            Transcribed command text
        """
        # TODO: Implement actual microphone audio capture
        # This would use PyAudio to capture from microphone and stream to Deepgram

        # Placeholder: In production, this would capture from microphone
        # For now, return mock transcript
        logger.info(f"Capturing audio for {timeout}s...")
        await asyncio.sleep(timeout)

        return "move forward 5 feet"  # Mock transcript

        # Real implementation would look like:
        # async def audio_generator():
        #     # Yield audio chunks from microphone
        #     pass
        #
        # transcript = await self.voice.transcribe_stream(
        #     audio_generator(),
        #     timeout=timeout
        # )
        # return transcript

    async def process_text_command(self, text: str) -> str:
        """
        Process a text command directly (without voice input)

        Useful for:
        - Testing
        - Web interface commands
        - Debugging

        Args:
            text: Command text

        Returns:
            Agent's response
        """
        logger.info(f"📝 Processing text command: \"{text}\"")

        try:
            # Process through agent
            response = await self.agent.process_command(text)

            # Optionally speak response
            # await self.voice.speak(response)

            return response

        except Exception as e:
            logger.error(f"Error processing text command: {e}")
            return f"Error: {str(e)}"

    def stop(self):
        """Stop the voice pipeline"""
        self._is_running = False
        self.wake_word.stop_listening()
        logger.info("Voice pipeline stop requested")

    def get_stats(self) -> dict:
        """Get pipeline statistics"""
        return {
            "running": self._is_running,
            "total_interactions": self._interaction_count,
            "agent_status": self.agent.get_agent_status(),
        }


class SimplePipeline:
    """
    Simplified pipeline for testing without wake word detection

    Just processes text commands through agent
    """

    def __init__(self, agent, voice_service=None):
        """
        Initialize simple pipeline

        Args:
            agent: ClaudeRobotAgent instance
            voice_service: Optional VoiceService for TTS
        """
        self.agent = agent
        self.voice = voice_service
        logger.info("SimplePipeline initialized (text-only mode)")

    async def process_command(self, text: str, speak_response: bool = False) -> str:
        """
        Process text command

        Args:
            text: Command text
            speak_response: If True, speak response via TTS

        Returns:
            Agent's response
        """
        logger.info(f"📝 Command: \"{text}\"")

        try:
            # Process through agent
            response = await self.agent.process_command(text)

            logger.info(f"💬 Response: \"{response}\"")

            # Optionally speak
            if speak_response and self.voice:
                await self.voice.speak(response)

            return response

        except Exception as e:
            logger.error(f"Error: {e}")
            return f"Error: {str(e)}"

    async def process_commands_interactive(self):
        """
        Interactive command loop (for testing)

        Prompts user for text commands and processes them
        """
        logger.info("\n" + "=" * 60)
        logger.info("Interactive Command Mode")
        logger.info("Type commands or 'quit' to exit")
        logger.info("=" * 60 + "\n")

        while True:
            try:
                # Get input (in production, this would be voice)
                command = input("You: ")

                if command.lower() in ["quit", "exit", "stop"]:
                    logger.info("Exiting interactive mode")
                    break

                if not command.strip():
                    continue

                # Process command
                response = await self.process_command(command)

                print(f"Dash: {response}\n")

            except KeyboardInterrupt:
                logger.info("\nExiting interactive mode")
                break
            except Exception as e:
                logger.error(f"Error: {e}")


async def create_full_pipeline(
    api_keys: dict,
    use_mock_robot: bool = False,
    use_mock_voice: bool = False,
    use_mock_wake_word: bool = False,
):
    """
    Factory function to create complete voice pipeline

    Args:
        api_keys: Dict with API keys:
            - anthropic_api_key
            - deepgram_api_key
            - porcupine_access_key
        use_mock_robot: Use mock robot service
        use_mock_voice: Use mock voice service
        use_mock_wake_word: Use mock wake word detector

    Returns:
        VoiceActionPipeline instance
    """
    from .robot_service import create_robot_service
    from .safety_validator import SafetyValidator
    from .voice_service import create_voice_service
    from .wake_word_service import create_wake_word_detector
    from .agent_service import create_agent

    logger.info("Creating full voice-to-action pipeline...")

    # 1. Robot service
    robot_service = create_robot_service(use_mock=use_mock_robot)

    if not use_mock_robot:
        logger.info("Connecting to robot...")
        connected = await robot_service.connect(timeout=30)
        if not connected:
            logger.warning("Could not connect to robot - using mock")
            robot_service = create_robot_service(use_mock=True)

    # 2. Safety validator
    safety = SafetyValidator(robot_service)

    # 3. Voice service
    voice = create_voice_service(
        api_key=api_keys.get("deepgram_api_key"),
        use_mock=use_mock_voice
    )

    # 4. Claude agent
    agent = create_agent(
        api_key=api_keys.get("anthropic_api_key"),
        robot_service=robot_service,
        safety_validator=safety,
        voice_service=voice,
    )

    # 5. Wake word detector
    wake_word = create_wake_word_detector(
        access_key=api_keys.get("porcupine_access_key"),
        use_mock=use_mock_wake_word
    )

    await wake_word.initialize()

    # 6. Create pipeline
    pipeline = VoiceActionPipeline(
        wake_word_detector=wake_word,
        voice_service=voice,
        agent=agent,
        robot_service=robot_service,
    )

    logger.info("✅ Full pipeline created and ready!")

    return pipeline


async def create_simple_pipeline(
    api_keys: dict,
    use_mock_robot: bool = False,
    use_mock_voice: bool = False,
):
    """
    Factory function to create simple text-based pipeline

    Args:
        api_keys: Dict with API keys
        use_mock_robot: Use mock robot service
        use_mock_voice: Use mock voice service

    Returns:
        SimplePipeline instance
    """
    from .robot_service import create_robot_service
    from .safety_validator import SafetyValidator
    from .voice_service import create_voice_service
    from .agent_service import create_agent

    logger.info("Creating simple text pipeline...")

    # Robot service
    robot_service = create_robot_service(use_mock=use_mock_robot)

    if not use_mock_robot:
        connected = await robot_service.connect(timeout=30)
        if not connected:
            logger.warning("Could not connect to robot - using mock")
            robot_service = create_robot_service(use_mock=True)

    # Safety validator
    safety = SafetyValidator(robot_service)

    # Voice service (optional)
    voice = create_voice_service(
        api_key=api_keys.get("deepgram_api_key"),
        use_mock=use_mock_voice
    ) if api_keys.get("deepgram_api_key") else None

    # Claude agent
    agent = create_agent(
        api_key=api_keys.get("anthropic_api_key"),
        robot_service=robot_service,
        safety_validator=safety,
        voice_service=voice,
    )

    # Create pipeline
    pipeline = SimplePipeline(agent=agent, voice_service=voice)

    logger.info("✅ Simple pipeline created!")

    return pipeline
