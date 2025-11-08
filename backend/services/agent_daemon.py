"""
Agent Daemon - Standalone Service Runner
Runs the robot AI agent as a daemon process
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import settings
from utils.logger import setup_logging
from services.voice_pipeline import create_full_pipeline, create_simple_pipeline

logger = logging.getLogger(__name__)


class AgentDaemon:
    """
    Agent daemon process

    Can run in two modes:
    1. Full voice mode: Wake word → STT → Agent → TTS
    2. Text mode: Simple text command processing (for testing)
    """

    def __init__(self, mode: str = "voice"):
        """
        Initialize daemon

        Args:
            mode: "voice" for full voice pipeline, "text" for simple text mode
        """
        self.mode = mode
        self.pipeline = None
        self._shutdown_event = asyncio.Event()

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"AgentDaemon initialized (mode: {mode})")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum} - initiating shutdown...")
        self._shutdown_event.set()

    async def start(self):
        """Start the daemon"""
        logger.info("=" * 70)
        logger.info("🤖 DASH ROBOT AI AGENT DAEMON")
        logger.info("=" * 70)
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info("=" * 70)

        try:
            # Validate API keys
            self._validate_config()

            # Create pipeline
            logger.info("\n🔧 Initializing pipeline...")
            await self._initialize_pipeline()

            # Run pipeline
            logger.info("\n✅ Pipeline ready!")

            if self.mode == "voice":
                await self._run_voice_mode()
            elif self.mode == "text":
                await self._run_text_mode()
            else:
                raise ValueError(f"Unknown mode: {self.mode}")

        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt received")
        except Exception as e:
            logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        finally:
            await self._shutdown()

    def _validate_config(self):
        """Validate required configuration"""
        logger.info("Validating configuration...")

        # Check Anthropic API key (required)
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        # Check Deepgram API key (required for voice mode)
        if self.mode == "voice" and not settings.DEEPGRAM_API_KEY:
            logger.warning("DEEPGRAM_API_KEY not set - voice features will be mocked")

        # Check Porcupine key (required for wake word)
        if self.mode == "voice" and not settings.PORCUPINE_ACCESS_KEY:
            logger.warning("PORCUPINE_ACCESS_KEY not set - wake word detection will be mocked")

        logger.info("✓ Configuration validated")

    async def _initialize_pipeline(self):
        """Initialize the appropriate pipeline"""
        api_keys = {
            "anthropic_api_key": settings.ANTHROPIC_API_KEY,
            "deepgram_api_key": settings.DEEPGRAM_API_KEY,
            "porcupine_access_key": settings.PORCUPINE_ACCESS_KEY,
        }

        if self.mode == "voice":
            self.pipeline = await create_full_pipeline(
                api_keys=api_keys,
                use_mock_robot=settings.ENVIRONMENT == "development",
                use_mock_voice=not settings.DEEPGRAM_API_KEY,
                use_mock_wake_word=not settings.PORCUPINE_ACCESS_KEY,
            )
        else:
            self.pipeline = await create_simple_pipeline(
                api_keys=api_keys,
                use_mock_robot=settings.ENVIRONMENT == "development",
                use_mock_voice=not settings.DEEPGRAM_API_KEY,
            )

    async def _run_voice_mode(self):
        """Run in full voice mode"""
        logger.info("\n" + "=" * 70)
        logger.info("🎙️  VOICE MODE - Listening for 'Hey Dash'...")
        logger.info("=" * 70 + "\n")

        # Start voice loop
        voice_task = asyncio.create_task(
            self.pipeline.run_continuous_loop()
        )

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Stop pipeline
        self.pipeline.stop()
        await asyncio.sleep(1.0)  # Give time to clean up

        voice_task.cancel()
        try:
            await voice_task
        except asyncio.CancelledError:
            pass

    async def _run_text_mode(self):
        """Run in text mode (interactive)"""
        logger.info("\n" + "=" * 70)
        logger.info("💬 TEXT MODE - Interactive Command Interface")
        logger.info("   Type commands or 'quit' to exit")
        logger.info("=" * 70 + "\n")

        # Run interactive loop
        try:
            await self.pipeline.process_commands_interactive()
        except Exception as e:
            logger.error(f"Error in text mode: {e}")

    async def _shutdown(self):
        """Clean up resources"""
        logger.info("\n" + "=" * 70)
        logger.info("🛑 SHUTDOWN")
        logger.info("=" * 70)

        if self.pipeline:
            logger.info("Stopping pipeline...")
            try:
                self.pipeline.stop()
            except:
                pass

        logger.info("✅ Shutdown complete")
        logger.info("=" * 70 + "\n")


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Dash Robot AI Agent Daemon")
    parser.add_argument(
        "--mode",
        choices=["voice", "text"],
        default="text",
        help="Operating mode: 'voice' for full voice pipeline, 'text' for interactive text mode"
    )
    args = parser.parse_args()

    # Create and start daemon
    daemon = AgentDaemon(mode=args.mode)
    await daemon.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
