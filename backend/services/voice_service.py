"""
Voice Service - Deepgram STT/TTS Integration
Handles speech-to-text and text-to-speech using Deepgram API
"""

from typing import Optional, AsyncGenerator
import asyncio
import logging
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    SpeakOptions,
)

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Voice processing service using Deepgram

    Capabilities:
    - Speech-to-Text (STT) via WebSocket streaming
    - Text-to-Speech (TTS) via Aura API
    - Audio playback integration
    """

    def __init__(
        self,
        api_key: str,
        stt_model: str = "flux-general-en",
        tts_model: str = "aura-asteria-en",
    ):
        """
        Initialize voice service

        Args:
            api_key: Deepgram API key
            stt_model: STT model (flux-general-en, nova-3, etc.)
            tts_model: TTS voice model (aura-asteria-en, etc.)
        """
        self.api_key = api_key
        self.stt_model = stt_model
        self.tts_model = tts_model

        # Initialize Deepgram client
        config = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        self.client = DeepgramClient(api_key, config)

        self._active_connection = None
        self._transcript_queue: Optional[asyncio.Queue] = None

        logger.info(f"VoiceService initialized (STT: {stt_model}, TTS: {tts_model})")

    # ==================== SPEECH-TO-TEXT ====================

    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        interim_results: bool = True,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Transcribe audio stream to text

        Args:
            audio_stream: Async generator yielding audio chunks
            interim_results: Return partial transcripts
            timeout: Maximum time to listen (seconds)

        Returns:
            Final transcript text
        """
        logger.info("Starting speech-to-text transcription...")

        self._transcript_queue = asyncio.Queue()
        transcript_parts = []

        # Create WebSocket connection
        dg_connection = self.client.listen.asyncwebsocket.v("1")

        # Event handlers
        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript

            if len(sentence) > 0:
                if result.is_final:
                    logger.info(f"📝 Final transcript: {sentence}")
                    transcript_parts.append(sentence)
                    await self._transcript_queue.put({"final": True, "text": sentence})
                elif interim_results:
                    logger.debug(f"📝 Interim: {sentence}")
                    await self._transcript_queue.put({"final": False, "text": sentence})

        async def on_error(self, error, **kwargs):
            logger.error(f"Deepgram STT error: {error}")

        async def on_close(self, close, **kwargs):
            logger.info("Deepgram STT connection closed")

        # Register event handlers
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)

        # Configure options
        options = LiveOptions(
            model=self.stt_model,
            language="en-US",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            interim_results=interim_results,
            endpointing=300,  # ms of silence to finalize utterance
            punctuate=True,
            smart_format=True,
        )

        # Start connection
        await dg_connection.start(options)
        self._active_connection = dg_connection

        try:
            # Stream audio with optional timeout
            if timeout:
                await asyncio.wait_for(
                    self._stream_audio(dg_connection, audio_stream),
                    timeout=timeout
                )
            else:
                await self._stream_audio(dg_connection, audio_stream)

        except asyncio.TimeoutError:
            logger.info("Transcription timeout reached")
        finally:
            # Finish connection
            await dg_connection.finish()
            self._active_connection = None

        # Return combined transcript
        final_transcript = " ".join(transcript_parts)
        logger.info(f"✅ Complete transcript: {final_transcript}")
        return final_transcript

    async def _stream_audio(self, connection, audio_stream):
        """Stream audio data to Deepgram"""
        async for audio_chunk in audio_stream:
            if len(audio_chunk) > 0:
                await connection.send(audio_chunk)
            await asyncio.sleep(0)  # Yield control

    async def transcribe_simple(self, text_prompt: str = "Say something...") -> str:
        """
        Simple transcription helper (for testing)

        In production, this would capture from microphone.
        For now, it's a placeholder.

        Args:
            text_prompt: Prompt to display

        Returns:
            Transcribed text
        """
        logger.info(f"{text_prompt}")

        # TODO: Implement actual microphone capture
        # For testing, return mock transcript
        return "Mock transcript - microphone integration pending"

    # ==================== TEXT-TO-SPEECH ====================

    async def speak(self, text: str, play_audio: bool = True) -> bytes:
        """
        Convert text to speech and optionally play it

        Args:
            text: Text to convert to speech
            play_audio: If True, play audio through speaker

        Returns:
            Audio data (WAV format)
        """
        logger.info(f"🔊 Speaking: \"{text[:100]}...\"")

        try:
            # Configure TTS options
            options = SpeakOptions(
                model=self.tts_model,
                encoding="linear16",
                sample_rate=24000,
            )

            # Generate speech
            response = await self.client.speak.asyncrest.v("1").stream(
                {"text": text},
                options
            )

            # Collect audio bytes
            audio_buffer = bytearray()
            async for chunk in response.aiter_bytes():
                audio_buffer.extend(chunk)

            audio_data = bytes(audio_buffer)

            logger.info(f"✅ Generated {len(audio_data)} bytes of audio")

            # Play audio if requested
            if play_audio:
                await self._play_audio(audio_data)

            return audio_data

        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise

    async def _play_audio(self, audio_data: bytes):
        """
        Play audio data through speaker

        This should be integrated with robot's speaker or system audio
        """
        logger.info(f"Playing {len(audio_data)} bytes of audio...")

        try:
            # Option 1: Save to temp file and play (simple approach)
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            # Play using system command (works on most Linux systems)
            # For Raspberry Pi, aplay should be available
            process = await asyncio.create_subprocess_exec(
                "aplay",
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            await process.communicate()

            # Clean up temp file
            os.remove(tmp_path)

            logger.info("✅ Audio playback completed")

        except FileNotFoundError:
            logger.warning("aplay not found - audio playback skipped (install alsa-utils)")
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    async def speak_stream(self, text_generator: AsyncGenerator[str, None]):
        """
        Stream TTS as text is being generated

        Args:
            text_generator: Async generator yielding text chunks

        This allows speaking responses as Claude generates them,
        reducing perceived latency.
        """
        sentence_buffer = ""

        async for text_chunk in text_generator:
            sentence_buffer += text_chunk

            # Speak complete sentences immediately
            if any(punct in text_chunk for punct in ['.', '!', '?']):
                await self.speak(sentence_buffer)
                sentence_buffer = ""

        # Speak any remaining text
        if sentence_buffer.strip():
            await self.speak(sentence_buffer)

    # ==================== UTILITY METHODS ====================

    async def get_transcript_stream(self) -> AsyncGenerator[dict, None]:
        """
        Get stream of transcript updates

        Yields:
            Dict with 'final' (bool) and 'text' (str)
        """
        if self._transcript_queue is None:
            logger.error("No active transcription")
            return

        while True:
            try:
                transcript = await asyncio.wait_for(
                    self._transcript_queue.get(),
                    timeout=0.1
                )
                yield transcript
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Transcript stream error: {e}")
                break

    async def test_connection(self) -> bool:
        """
        Test Deepgram API connection

        Returns:
            True if connection successful
        """
        try:
            # Simple test with pre-recorded audio URL
            test_url = "https://static.deepgram.com/examples/interview_speech-analytics.wav"

            response = await self.client.listen.rest.v("1").transcribe_url(
                {"url": test_url}
            )

            logger.info("✅ Deepgram connection test successful")
            return True

        except Exception as e:
            logger.error(f"❌ Deepgram connection test failed: {e}")
            return False


class MockVoiceService:
    """Mock voice service for testing without API key"""

    def __init__(self, *args, **kwargs):
        logger.info("MockVoiceService initialized (for testing)")

    async def transcribe_stream(self, audio_stream, **kwargs) -> str:
        """Mock transcription"""
        logger.info("Mock: Transcribing audio stream...")
        await asyncio.sleep(1.0)
        return "This is a mock transcript for testing"

    async def transcribe_simple(self, text_prompt: str = "") -> str:
        """Mock simple transcription"""
        logger.info(f"Mock: {text_prompt}")
        await asyncio.sleep(0.5)
        return "Mock transcript text"

    async def speak(self, text: str, play_audio: bool = True) -> bytes:
        """Mock TTS"""
        logger.info(f"Mock: Speaking '{text[:50]}...'")
        await asyncio.sleep(0.5)
        return b"mock_audio_data"

    async def speak_stream(self, text_generator):
        """Mock streaming TTS"""
        async for chunk in text_generator:
            logger.info(f"Mock: Speaking chunk '{chunk[:30]}...'")
            await asyncio.sleep(0.3)

    async def test_connection(self) -> bool:
        """Mock connection test"""
        logger.info("Mock: Connection test (always succeeds)")
        return True


# Factory function
def create_voice_service(api_key: Optional[str] = None, use_mock: bool = False, **kwargs):
    """
    Create voice service instance

    Args:
        api_key: Deepgram API key (required if use_mock=False)
        use_mock: If True, return MockVoiceService
        **kwargs: Additional arguments for VoiceService

    Returns:
        VoiceService or MockVoiceService instance
    """
    if use_mock or not api_key:
        if not use_mock:
            logger.warning("No API key provided - using MockVoiceService")
        return MockVoiceService()
    else:
        return VoiceService(api_key=api_key, **kwargs)
