"""
Wake Word Detection Service
Listens for "Hey Dash" wake word using Porcupine
"""

import asyncio
import logging
from typing import Optional, Callable
import pyaudio
import struct

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Wake word detection using Picovoice Porcupine

    Listens continuously for wake word ("Hey Dash") on-device
    with minimal CPU/battery impact.
    """

    def __init__(
        self,
        access_key: str,
        keyword: str = "hey dash",
        sensitivity: float = 0.5,
    ):
        """
        Initialize wake word detector

        Args:
            access_key: Picovoice access key
            keyword: Wake word to detect
            sensitivity: Detection sensitivity (0.0 - 1.0)
        """
        self.access_key = access_key
        self.keyword = keyword
        self.sensitivity = sensitivity

        self._porcupine = None
        self._audio_stream = None
        self._is_listening = False

        logger.info(f"WakeWordDetector initialized (keyword: '{keyword}')")

    async def initialize(self):
        """Initialize Porcupine and audio stream"""
        try:
            import pvporcupine

            # Create Porcupine instance
            # For custom wake words, you would use keyword_paths
            # For built-in keywords, use keywords parameter
            self._porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.keyword],  # or use built-in keywords
                sensitivities=[self.sensitivity]
            )

            logger.info(f"✅ Porcupine initialized (sample rate: {self._porcupine.sample_rate}Hz, frame length: {self._porcupine.frame_length})")

        except ImportError:
            logger.error("pvporcupine not installed. Install with: pip install pvporcupine")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            raise

    async def start_listening(self, on_wake_word_detected: Optional[Callable] = None):
        """
        Start listening for wake word

        Args:
            on_wake_word_detected: Callback function called when wake word detected
        """
        if self._porcupine is None:
            await self.initialize()

        self._is_listening = True
        logger.info(f"👂 Listening for '{self.keyword}'...")

        # Open audio stream
        pa = pyaudio.PyAudio()

        try:
            self._audio_stream = pa.open(
                rate=self._porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self._porcupine.frame_length,
            )

            # Listen loop
            while self._is_listening:
                # Read audio frame
                pcm = self._audio_stream.read(
                    self._porcupine.frame_length,
                    exception_on_overflow=False
                )

                # Convert to int16 array
                pcm = struct.unpack_from(
                    "h" * self._porcupine.frame_length,
                    pcm
                )

                # Process frame
                keyword_index = self._porcupine.process(pcm)

                if keyword_index >= 0:
                    logger.info(f"🎙️ Wake word detected: '{self.keyword}'")

                    # Call callback if provided
                    if on_wake_word_detected:
                        if asyncio.iscoroutinefunction(on_wake_word_detected):
                            await on_wake_word_detected()
                        else:
                            on_wake_word_detected()

                # Yield control to event loop
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
        finally:
            if self._audio_stream:
                self._audio_stream.close()
            pa.terminate()

    async def detect_once(self, timeout: float = 30.0) -> bool:
        """
        Listen for wake word once with timeout

        Args:
            timeout: Maximum time to wait (seconds)

        Returns:
            True if wake word detected, False if timeout
        """
        logger.info(f"Listening for '{self.keyword}' (timeout: {timeout}s)...")

        detected = False

        def on_detected():
            nonlocal detected
            detected = True

        # Start listening with callback
        listen_task = asyncio.create_task(
            self.start_listening(on_wake_word_detected=on_detected)
        )

        try:
            # Wait for detection or timeout
            start_time = asyncio.get_event_loop().time()

            while not detected:
                await asyncio.sleep(0.1)

                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.info("Wake word detection timeout")
                    break

        finally:
            # Stop listening
            self._is_listening = False
            await asyncio.sleep(0.2)  # Give time to clean up
            listen_task.cancel()

        return detected

    def stop_listening(self):
        """Stop listening for wake word"""
        self._is_listening = False
        logger.info("Wake word detection stopped")

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()

        if self._porcupine:
            self._porcupine.delete()
            self._porcupine = None

        logger.info("Wake word detector cleaned up")

    def __del__(self):
        """Destructor"""
        self.cleanup()


class MockWakeWordDetector:
    """Mock wake word detector for testing"""

    def __init__(self, *args, **kwargs):
        logger.info("MockWakeWordDetector initialized (for testing)")
        self._is_listening = False

    async def initialize(self):
        """Mock initialization"""
        logger.info("Mock: Wake word detector initialized")

    async def start_listening(self, on_wake_word_detected: Optional[Callable] = None):
        """Mock listening"""
        self._is_listening = True
        logger.info("Mock: Listening for wake word...")

        # Simulate detecting wake word every 10 seconds
        while self._is_listening:
            await asyncio.sleep(10.0)

            if self._is_listening:
                logger.info("Mock: Wake word detected!")
                if on_wake_word_detected:
                    if asyncio.iscoroutinefunction(on_wake_word_detected):
                        await on_wake_word_detected()
                    else:
                        on_wake_word_detected()

    async def detect_once(self, timeout: float = 30.0) -> bool:
        """Mock single detection"""
        logger.info(f"Mock: Waiting for wake word (timeout: {timeout}s)")
        await asyncio.sleep(2.0)  # Simulate brief wait
        logger.info("Mock: Wake word detected!")
        return True

    def stop_listening(self):
        """Mock stop"""
        self._is_listening = False
        logger.info("Mock: Wake word detection stopped")

    def cleanup(self):
        """Mock cleanup"""
        logger.info("Mock: Cleaned up")


# Factory function
def create_wake_word_detector(
    access_key: Optional[str] = None,
    use_mock: bool = False,
    **kwargs
):
    """
    Create wake word detector instance

    Args:
        access_key: Picovoice access key
        use_mock: If True, return MockWakeWordDetector
        **kwargs: Additional arguments for WakeWordDetector

    Returns:
        WakeWordDetector or MockWakeWordDetector instance
    """
    if use_mock or not access_key:
        if not use_mock:
            logger.warning("No Porcupine access key - using MockWakeWordDetector")
        return MockWakeWordDetector()
    else:
        return WakeWordDetector(access_key=access_key, **kwargs)
