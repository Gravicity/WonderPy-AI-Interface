# Deepgram API Integration for Voice Processing

**Research Date**: 2025-11-08
**Purpose**: Cost-effective, high-quality voice processing for autonomous robot AI

---

## Executive Summary

Deepgram provides a unified voice AI platform offering both Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities with exceptional performance and cost efficiency. This document outlines the integration strategy for the WonderPy AI-Autonomous Robot Platform.

**Key Benefits**:
- **59% cost savings** compared to Whisper + ElevenLabs stack
- **Sub-200ms latency** for real-time conversations
- **WebSocket streaming** for continuous audio processing
- **On-device VAD** integration with Silero for optimal wake word handling
- **Unified API** simplifying voice pipeline architecture

---

## Cost Analysis

### Deepgram Pricing (Pay-as-you-go)

**Speech-to-Text (Nova-3 / Flux)**:
- Streaming: **$0.0077/minute** ($0.462/hour)
- Pre-recorded: $0.0043/minute
- Recommended: Nova-3 for general use, Flux for conversational AI

**Text-to-Speech (Aura-2)**:
- **$0.015 per 1,000 characters** (~150 words)
- Sub-200ms latency (industry-leading)
- Neural voices with emotional range

### Comparison vs. Previous Stack

| Component | Previous Stack | Deepgram | Savings |
|-----------|---------------|----------|---------|
| STT | Whisper Cloud: $0.006/min | Nova-3: $0.0077/min | -28% |
| TTS | ElevenLabs: $0.05/min (~300 chars) | Aura-2: $0.0045/min (300 chars) | **91%** |
| **Total** | **$0.056/min** | **$0.0122/min** | **78%** |

**Estimated Monthly Cost** (1 hour/day usage):
- Previous: ~$100/month
- Deepgram: ~$22/month
- **Savings: $78/month (78%)**

For typical robot usage (30 min/day):
- **$11/month vs. $50/month = $39/month savings**

---

## Technical Architecture

### 1. Speech-to-Text (STT) Pipeline

#### Model Selection

**Nova-3** (Recommended for robot):
- Optimized for real-time streaming
- Excellent accuracy for command-style speech
- Lower latency than Nova-2

**Flux** (Alternative for conversational AI):
- Optimized for conversations and natural dialogue
- Better handling of informal speech patterns
- Ideal for "Hey Dash, what's the weather?" style queries

#### WebSocket Streaming Implementation

```python
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import asyncio

# Initialize Deepgram client
deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

async def transcribe_audio_stream():
    """Real-time audio transcription using WebSocket"""

    # Create WebSocket connection
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    # Event handlers
    async def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) > 0:
            if result.is_final:
                # Final transcript - send to Claude agent
                print(f"Final: {sentence}")
                await process_command(sentence)
            else:
                # Interim result - can show in UI
                print(f"Interim: {sentence}")

    async def on_error(self, error, **kwargs):
        print(f"Error: {error}")

    async def on_close(self, close, **kwargs):
        print("Connection closed")

    # Register event handlers
    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
    dg_connection.on(LiveTranscriptionEvents.Error, on_error)
    dg_connection.on(LiveTranscriptionEvents.Close, on_close)

    # Configure streaming options
    options = LiveOptions(
        model="nova-3",  # or "flux-general-en" for conversational
        language="en-US",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        interim_results=True,  # Get partial results
        endpointing=300,  # ms of silence to finalize utterance
        punctuate=True,
        smart_format=True,  # Auto-capitalization, formatting
    )

    # Start connection
    await dg_connection.start(options)

    # Stream audio data
    async for audio_chunk in audio_input_stream():
        await dg_connection.send(audio_chunk)

    # Close connection
    await dg_connection.finish()
```

#### Raspberry Pi Audio Capture

```python
import pyaudio
import asyncio
from collections import deque

# Audio configuration
CHUNK_SIZE = 8192  # Frames per buffer
FORMAT = pyaudio.paInt16  # 16-bit PCM
CHANNELS = 1  # Mono
RATE = 16000  # 16kHz sample rate

async def capture_robot_microphone():
    """Capture audio from robot's microphone"""

    audio = pyaudio.PyAudio()

    # Open microphone stream
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
        input_device_index=get_robot_mic_index()  # USB mic or I2S
    )

    audio_queue = deque(maxlen=10)

    try:
        while True:
            # Read audio chunk
            audio_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_queue.append(audio_data)
            yield audio_data
            await asyncio.sleep(0)  # Yield control

    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
```

#### VAD Integration (Silero VAD)

```python
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

# Load Silero VAD model (runs on-device)
model = load_silero_vad()

def is_speech_active(audio_chunk: bytes, sample_rate: int = 16000) -> bool:
    """Detect if audio contains speech using Silero VAD"""

    # Convert bytes to tensor
    audio_tensor = torch.frombuffer(audio_chunk, dtype=torch.int16).float()
    audio_tensor = audio_tensor / 32768.0  # Normalize to [-1, 1]

    # Get speech probability
    speech_prob = model(audio_tensor, sample_rate).item()

    # Threshold for speech detection (0.5 = 50% confidence)
    return speech_prob > 0.5

async def vad_filtered_stream():
    """Stream audio only when speech is detected"""

    async for audio_chunk in capture_robot_microphone():
        if is_speech_active(audio_chunk):
            yield audio_chunk
        # Discard silence to save bandwidth and costs
```

---

### 2. Text-to-Speech (TTS) Pipeline

#### Aura-2 TTS Implementation

```python
from deepgram import DeepgramClient, SpeakOptions

async def speak_response(text: str, voice: str = "aura-asteria-en"):
    """
    Convert text to speech and play through robot speaker

    Available voices:
    - aura-asteria-en: Friendly female (good for educational robot)
    - aura-luna-en: Warm, conversational female
    - aura-stella-en: Clear, energetic female
    - aura-athena-en: Professional female
    - aura-orion-en: Friendly male
    """

    deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    # Configure TTS options
    options = SpeakOptions(
        model="aura-asteria-en",  # Voice model
        encoding="linear16",  # PCM format
        sample_rate=24000,  # 24kHz for quality
    )

    # Generate speech (streaming for low latency)
    response = await deepgram.speak.asyncrest.v("1").stream(
        {"text": text},
        options
    )

    # Stream audio to robot speaker
    audio_buffer = bytearray()
    async for chunk in response.aiter_bytes():
        audio_buffer.extend(chunk)

    # Play through robot speaker
    await play_audio_on_robot(bytes(audio_buffer))

    return len(text)  # Return character count for cost tracking
```

#### Cost-Optimized Response Streaming

```python
async def stream_tts_response(text_generator):
    """
    Stream TTS as text is generated by Claude
    Reduces perceived latency
    """

    sentence_buffer = ""

    async for text_chunk in text_generator:
        sentence_buffer += text_chunk

        # Send complete sentences to TTS immediately
        if any(punct in text_chunk for punct in ['.', '!', '?']):
            await speak_response(sentence_buffer)
            sentence_buffer = ""

    # Speak any remaining text
    if sentence_buffer.strip():
        await speak_response(sentence_buffer)
```

---

### 3. Complete Voice Pipeline Integration

#### Wake Word → STT → Claude → TTS Flow

```python
from pvporcupine import create
import asyncio

class VoiceInteractionPipeline:
    """Complete voice interaction system for robot"""

    def __init__(self, deepgram_key: str, porcupine_key: str):
        self.deepgram = DeepgramClient(api_key=deepgram_key)
        self.porcupine = create(
            access_key=porcupine_key,
            keywords=["hey dash"]  # Custom wake word
        )
        self.claude_agent = ClaudeAgentService()

    async def run_voice_loop(self):
        """Main voice interaction loop"""

        print("🎤 Voice pipeline active. Listening for 'Hey Dash'...")

        while True:
            # 1. Wake Word Detection (Porcupine - local, no cost)
            if await self.detect_wake_word():
                print("🔊 Wake word detected!")

                # 2. Play acknowledgment sound
                await self.play_beep()

                # 3. Capture user command (Deepgram STT)
                command_text = await self.transcribe_command()
                print(f"📝 Heard: {command_text}")

                # 4. Send to Claude agent for processing
                response_stream = await self.claude_agent.process_command(
                    command_text
                )

                # 5. Stream response to TTS (Deepgram Aura)
                async for response_chunk in response_stream:
                    if response_chunk.get("type") == "text":
                        await self.speak_response(response_chunk["text"])

                print("✅ Interaction complete\n")

    async def detect_wake_word(self) -> bool:
        """Listen for wake word using Porcupine"""
        # See Porcupine integration doc for details
        pass

    async def transcribe_command(self, timeout: float = 5.0) -> str:
        """Capture and transcribe voice command"""

        dg_connection = self.deepgram.listen.asyncwebsocket.v("1")

        transcript_parts = []

        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if result.is_final and len(sentence) > 0:
                transcript_parts.append(sentence)

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="flux-general-en",  # Conversational model
            encoding="linear16",
            sample_rate=16000,
            interim_results=False,  # Only final results
            endpointing=300,
        )

        await dg_connection.start(options)

        # Stream audio with timeout
        start_time = asyncio.get_event_loop().time()
        async for audio_chunk in capture_robot_microphone():
            await dg_connection.send(audio_chunk)

            if asyncio.get_event_loop().time() - start_time > timeout:
                break

        await dg_connection.finish()

        return " ".join(transcript_parts)

    async def speak_response(self, text: str):
        """Convert text to speech and play"""

        options = SpeakOptions(
            model="aura-asteria-en",
            encoding="linear16",
            sample_rate=24000,
        )

        response = await self.deepgram.speak.asyncrest.v("1").stream(
            {"text": text},
            options
        )

        audio_buffer = bytearray()
        async for chunk in response.aiter_bytes():
            audio_buffer.extend(chunk)

        await play_audio_on_robot(bytes(audio_buffer))
```

---

## FastAPI Integration

### Voice Endpoints

```python
# backend/api/routes/voice.py
from fastapi import APIRouter, WebSocket, HTTPException
from deepgram import DeepgramClient, LiveOptions, SpeakOptions
import asyncio

router = APIRouter()

@router.websocket("/stream/stt")
async def websocket_speech_to_text(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech-to-text
    Used by web UI for voice commands (secondary to on-robot mic)
    """
    await websocket.accept()

    deepgram = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
    dg_connection = deepgram.listen.asyncwebsocket.v("1")

    transcript_queue = asyncio.Queue()

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if len(transcript) > 0:
            response = {
                "type": "transcript",
                "transcript": transcript,
                "is_final": result.is_final,
                "confidence": result.channel.alternatives[0].confidence,
            }
            await transcript_queue.put(response)

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=16000,
        interim_results=True,
        endpointing=300,
    )

    await dg_connection.start(options)

    # Handle bidirectional communication
    async def receive_audio():
        try:
            while True:
                message = await websocket.receive_bytes()
                await dg_connection.send(message)
        except Exception as e:
            print(f"Receive error: {e}")

    async def send_transcripts():
        try:
            while True:
                transcript = await transcript_queue.get()
                await websocket.send_json(transcript)
        except Exception as e:
            print(f"Send error: {e}")

    await asyncio.gather(receive_audio(), send_transcripts())

    await dg_connection.finish()


@router.post("/speak")
async def text_to_speech(text: str, voice: str = "aura-asteria-en"):
    """
    Generate speech from text using Deepgram Aura
    Returns audio file or streams to robot speaker
    """
    deepgram = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

    options = SpeakOptions(
        model=voice,
        encoding="linear16",
        sample_rate=24000,
    )

    response = await deepgram.speak.asyncrest.v("1").stream(
        {"text": text},
        options
    )

    # Collect audio bytes
    audio_data = bytearray()
    async for chunk in response.aiter_bytes():
        audio_data.extend(chunk)

    # Send to robot speaker service
    await robot_speaker_service.play_audio(bytes(audio_data))

    return {
        "status": "success",
        "characters": len(text),
        "estimated_cost": len(text) * 0.000015  # $0.015 per 1K chars
    }
```

---

## Performance Optimization

### 1. Audio Buffer Management

```python
class AudioBufferManager:
    """Efficient audio buffering for streaming"""

    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self.buffer = bytearray()

    def add_chunk(self, audio_data: bytes):
        """Add audio chunk to buffer"""
        self.buffer.extend(audio_data)

    def get_chunks(self, size: int = None):
        """Get buffered chunks for sending"""
        size = size or self.chunk_size

        while len(self.buffer) >= size:
            chunk = bytes(self.buffer[:size])
            self.buffer = self.buffer[size:]
            yield chunk
```

### 2. Latency Reduction Strategies

- **Use VAD pre-filtering**: Only send audio when speech detected (saves bandwidth)
- **Enable interim results**: Show user feedback while processing
- **Stream TTS responses**: Don't wait for full Claude response
- **Local wake word**: Porcupine runs on-device (no latency)
- **Persistent WebSocket**: Reuse connection instead of reconnecting

### 3. Cost Optimization

```python
class VoiceCostTracker:
    """Track and optimize voice processing costs"""

    def __init__(self):
        self.stt_minutes = 0.0
        self.tts_characters = 0

    def log_stt_usage(self, duration_seconds: float):
        """Log STT usage"""
        minutes = duration_seconds / 60.0
        self.stt_minutes += minutes
        cost = minutes * 0.0077  # Nova-3 streaming rate

        print(f"STT: {duration_seconds:.1f}s (${cost:.4f})")

    def log_tts_usage(self, character_count: int):
        """Log TTS usage"""
        self.tts_characters += character_count
        cost = (character_count / 1000) * 0.015

        print(f"TTS: {character_count} chars (${cost:.4f})")

    def get_daily_estimate(self) -> dict:
        """Estimate daily costs"""
        stt_cost = self.stt_minutes * 0.0077
        tts_cost = (self.tts_characters / 1000) * 0.015

        return {
            "stt_minutes": self.stt_minutes,
            "stt_cost": stt_cost,
            "tts_characters": self.tts_characters,
            "tts_cost": tts_cost,
            "total_cost": stt_cost + tts_cost,
        }
```

---

## Raspberry Pi Setup

### Installation

```bash
# Install Python SDK
pip install deepgram-sdk==3.9.0

# Install audio dependencies
sudo apt-get install portaudio19-dev python3-pyaudio

# Install Silero VAD
pip install silero-vad==0.1.0

# Install Porcupine wake word
pip install pvporcupine==3.0.3
```

### Environment Configuration

```bash
# Add to .env
DEEPGRAM_API_KEY="your-deepgram-api-key"
PORCUPINE_ACCESS_KEY="your-picovoice-access-key"

# Voice configuration
VOICE_MODEL_STT="flux-general-en"  # or "nova-3"
VOICE_MODEL_TTS="aura-asteria-en"
WAKE_WORD="hey dash"
```

---

## Testing & Debugging

### Test STT Accuracy

```python
async def test_stt_accuracy():
    """Test speech recognition accuracy"""

    test_phrases = [
        "Hey Dash, move forward 5 feet",
        "What's the weather like today?",
        "Turn left 90 degrees",
        "Tell me a joke",
    ]

    for phrase in test_phrases:
        # Play pre-recorded audio
        audio = load_test_audio(phrase)
        transcript = await transcribe_audio(audio)

        # Calculate word error rate
        wer = calculate_wer(phrase, transcript)
        print(f"Expected: {phrase}")
        print(f"Got: {transcript}")
        print(f"WER: {wer:.2%}\n")
```

### Monitor Latency

```python
import time

async def measure_voice_latency():
    """Measure end-to-end voice interaction latency"""

    # 1. Wake word detection time
    wake_start = time.time()
    await detect_wake_word()
    wake_latency = time.time() - wake_start

    # 2. STT latency
    stt_start = time.time()
    command = await transcribe_command()
    stt_latency = time.time() - stt_start

    # 3. Claude processing latency
    claude_start = time.time()
    response = await claude_agent.process(command)
    claude_latency = time.time() - claude_start

    # 4. TTS latency
    tts_start = time.time()
    await speak_response(response)
    tts_latency = time.time() - tts_start

    total_latency = time.time() - wake_start

    print(f"""
    Voice Pipeline Latency:
    - Wake word: {wake_latency:.3f}s
    - STT: {stt_latency:.3f}s
    - Claude: {claude_latency:.3f}s
    - TTS: {tts_latency:.3f}s
    - Total: {total_latency:.3f}s
    """)
```

---

## Security Considerations

### API Key Protection

```python
# NEVER hardcode keys
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Validate key on startup
if not DEEPGRAM_API_KEY:
    raise ValueError("DEEPGRAM_API_KEY environment variable not set")

# Use key rotation
async def validate_api_key():
    """Validate Deepgram API key"""
    try:
        client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        # Test with minimal request
        await client.listen.rest.v("1").transcribe_url(
            {"url": "https://static.deepgram.com/examples/interview_speech-analytics.wav"}
        )
        return True
    except Exception as e:
        logger.error(f"Invalid Deepgram API key: {e}")
        return False
```

### Audio Privacy

- **Local processing first**: Use VAD and wake word detection locally before sending to cloud
- **Audio not stored**: Deepgram doesn't store audio by default (verify settings)
- **User consent**: Inform users that voice is processed via cloud API
- **Mute button**: Hardware button to disable microphone

---

## Conclusion

Deepgram provides an excellent voice processing solution for the WonderPy AI robot platform with:

- **78% cost savings** compared to previous stack
- **Sub-200ms TTS latency** for natural conversations
- **Unified API** simplifying development
- **Production-ready** WebSocket streaming

The integration with Silero VAD and Porcupine wake word creates a complete on-device voice pipeline that minimizes cloud costs while maintaining exceptional quality.

**Next Steps**:
1. Implement voice pipeline service in `backend/services/voice_pipeline.py`
2. Add wake word detection with Porcupine
3. Integrate with Claude agent for command processing
4. Add cost tracking and monitoring
5. Test end-to-end latency on Raspberry Pi
6. Optimize for battery usage and network bandwidth
