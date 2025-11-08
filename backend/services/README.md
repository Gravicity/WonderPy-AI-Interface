# Robot AI Services

This directory contains the core services for the autonomous AI-powered Dash robot.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Voice-to-Action Pipeline                     │
│                                                                  │
│  Wake Word → STT → Claude Agent → Robot Actions → TTS           │
│  (Porcupine) (Deepgram) (Anthropic)  (WonderPy)   (Deepgram)   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Services

### 1. Robot Service (`robot_service.py`)
**Purpose**: Hardware abstraction layer for Dash robot control

**Features**:
- Abstract interface for robot commands
- Real WonderPy implementation
- Mock implementation for testing
- Movement, sensors, lights, head, sound control

**Usage**:
```python
from services.robot_service import create_robot_service

# Create robot service
robot = create_robot_service(use_mock=False)

# Connect to robot
await robot.connect(timeout=30)

# Move robot
await robot.move_forward(distance_cm=30.48, speed_cm_s=20)

# Check sensors
sensors = await robot.get_distance_sensors()
print(f"Front distance: {sensors['front_cm']}cm")

# Set lights
await robot.set_lights(color="blue", location="all")
```

### 2. Safety Validator (`safety_validator.py`)
**Purpose**: Multi-tier safety validation before executing commands

**Features**:
- Hardware limit checks
- Obstacle detection
- Battery monitoring
- Strict/permissive modes

**Usage**:
```python
from services.safety_validator import SafetyValidator

safety = SafetyValidator(robot_service)

# Validate movement
result = await safety.validate_movement("forward", distance_cm=100, speed_cm_s=20)

if result.safe:
    await robot.move_forward(100, 20)
else:
    print(f"⚠️ {result.reason}")
    print(f"Suggested: {result.suggested_action}")
```

### 3. Robot Tools (`robot_tools.py`)
**Purpose**: Define tools for Claude agent to control robot

**Features**:
- 10 core tools (move, turn, sensors, lights, head, sound, speak)
- Integrated safety validation
- Structured tool results for Claude
- Error handling

**Tools Available**:
- `move_forward` - Move robot forward with safety checks
- `move_backward` - Move robot backward
- `turn` - Turn robot (positive = clockwise)
- `stop` - Emergency stop
- `check_sensors` - Read distance sensors
- `get_battery` - Check battery level
- `set_lights` - Change LED colors
- `move_head` - Pan/tilt head
- `play_tone` - Beep sounds
- `speak` - Text-to-speech

### 4. Voice Service (`voice_service.py`)
**Purpose**: Deepgram STT/TTS integration

**Features**:
- WebSocket streaming STT
- Aura TTS with audio playback
- Mock implementation for testing

**Usage**:
```python
from services.voice_service import create_voice_service

voice = create_voice_service(
    api_key=DEEPGRAM_API_KEY,
    stt_model="flux-general-en",
    tts_model="aura-asteria-en"
)

# Text-to-Speech
await voice.speak("Hello! I'm Dash the robot.")

# Speech-to-Text (requires audio stream)
# transcript = await voice.transcribe_stream(audio_stream, timeout=5.0)
```

### 5. Wake Word Detector (`wake_word_service.py`)
**Purpose**: Porcupine wake word detection ("Hey Dash")

**Features**:
- On-device wake word detection
- Continuous listening mode
- Single detection with timeout
- Mock implementation for testing

**Usage**:
```python
from services.wake_word_service import create_wake_word_detector

wake_word = create_wake_word_detector(
    access_key=PORCUPINE_ACCESS_KEY,
    keyword="hey dash"
)

await wake_word.initialize()

# Detect once with timeout
detected = await wake_word.detect_once(timeout=30.0)

if detected:
    print("Wake word detected!")
```

### 6. Claude Agent Service (`agent_service.py`)
**Purpose**: Autonomous AI agent using Claude Code SDK

**Features**:
- Natural language command processing
- Tool orchestration
- Multi-step reasoning
- Conversation context management
- Safety-conscious personality

**Usage**:
```python
from services.agent_service import create_agent

agent = create_agent(
    api_key=ANTHROPIC_API_KEY,
    robot_service=robot,
    safety_validator=safety,
    voice_service=voice
)

# Process command
response = await agent.process_command("move forward 5 feet")
print(response)

# Agent autonomously:
# 1. Converts 5 feet to 152.4 cm
# 2. Calls check_sensors tool
# 3. Validates safety
# 4. Calls move_forward tool
# 5. Returns friendly response
```

### 7. Voice Pipeline (`voice_pipeline.py`)
**Purpose**: Complete voice-to-action pipeline coordinator

**Features**:
- Continuous voice interaction loop
- Full pipeline: Wake word → STT → Agent → TTS
- Simple text-only pipeline for testing

**Usage**:
```python
from services.voice_pipeline import create_full_pipeline

# Create full voice pipeline
pipeline = await create_full_pipeline(
    api_keys={
        "anthropic_api_key": ANTHROPIC_API_KEY,
        "deepgram_api_key": DEEPGRAM_API_KEY,
        "porcupine_access_key": PORCUPINE_ACCESS_KEY,
    },
    use_mock_robot=False
)

# Run continuous loop
await pipeline.run_continuous_loop()

# User says: "Hey Dash, move forward 5 feet"
# Pipeline:
# 1. Detects "Hey Dash"
# 2. Plays beep
# 3. Transcribes "move forward 5 feet"
# 4. Agent processes and executes
# 5. Speaks response
# 6. Returns to listening
```

### 8. Agent Daemon (`agent_daemon.py`)
**Purpose**: Standalone daemon process

**Features**:
- Voice mode (full pipeline)
- Text mode (interactive testing)
- Signal handling
- Configuration validation

**Usage**:
```bash
# Text mode (interactive testing)
python -m backend.services.agent_daemon --mode text

# Voice mode (full pipeline)
python -m backend.services.agent_daemon --mode voice
```

## Quick Start

### 1. Testing with Mock Robot

```python
import asyncio
from services.voice_pipeline import create_simple_pipeline

async def main():
    pipeline = await create_simple_pipeline(
        api_keys={"anthropic_api_key": "your-key"},
        use_mock_robot=True,
        use_mock_voice=True
    )

    # Test commands
    response = await pipeline.process_command("move forward 1 meter")
    print(response)

    response = await pipeline.process_command("turn around")
    print(response)

asyncio.run(main())
```

### 2. Interactive Text Mode

```bash
cd /home/user/WonderPy-AI-Interface

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-your-key"

# Run interactive mode
python -m backend.services.agent_daemon --mode text
```

Then type commands:
```
You: move forward 5 feet
Dash: Okay! Let me check for obstacles first... All clear! I'll move forward 5 feet...

You: what's your battery?
Dash: My battery is at 85% - plenty of power!

You: turn left 90 degrees
Dash: Sure! I'll turn 90 degrees counter-clockwise...
```

### 3. Full Voice Pipeline (Production)

```bash
# Set all API keys
export ANTHROPIC_API_KEY="sk-ant-your-key"
export DEEPGRAM_API_KEY="your-deepgram-key"
export PORCUPINE_ACCESS_KEY="your-porcupine-key"

# Run voice mode
python -m backend.services.agent_daemon --mode voice
```

## Testing

### Unit Tests

```bash
# Test robot service
pytest backend/tests/test_robot_service.py

# Test safety validator
pytest backend/tests/test_safety_validator.py

# Test agent service
pytest backend/tests/test_agent_service.py
```

### Manual Testing Checklist

- [ ] Robot connection works
- [ ] Movement commands execute safely
- [ ] Obstacle detection prevents collisions
- [ ] Battery check warnings work
- [ ] Lights change colors correctly
- [ ] Head movement works
- [ ] Tones play
- [ ] TTS speaks responses
- [ ] Wake word detection triggers
- [ ] Full voice loop completes
- [ ] Agent uses tools correctly
- [ ] Multi-step commands work

## Configuration

All services use settings from `backend/utils/config.py`:

```python
# Required
ANTHROPIC_API_KEY="sk-ant-..."

# For voice features
DEEPGRAM_API_KEY="..."
PORCUPINE_ACCESS_KEY="..."
VOICE_MODEL_STT="flux-general-en"
VOICE_MODEL_TTS="aura-asteria-en"
WAKE_WORD="hey dash"

# Robot settings
ROBOT_SCAN_TIMEOUT=20
ROBOT_CONNECTION_TIMEOUT=30
```

## Deployment

### As Systemd Service

Create `/etc/systemd/system/dash-agent.service`:

```ini
[Unit]
Description=Dash Robot AI Agent
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/WonderPy-AI-Interface
Environment="ANTHROPIC_API_KEY=your-key"
Environment="DEEPGRAM_API_KEY=your-key"
Environment="PORCUPINE_ACCESS_KEY=your-key"
ExecStart=/home/pi/WonderPy-AI-Interface/venv/bin/python -m backend.services.agent_daemon --mode voice
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable dash-agent
sudo systemctl start dash-agent
sudo systemctl status dash-agent
```

## Troubleshooting

### Robot won't connect
- Check Bluetooth is enabled: `sudo systemctl status bluetooth`
- Verify robot is powered on and in range
- Try: `sudo hcitool scan` to see if robot is visible
- Check WonderPy installed: `pip show WonderPy`

### Voice features not working
- Verify API keys are set
- Check microphone: `arecord -l`
- Check speaker: `aplay -l`
- Test Deepgram connection: `curl` their API
- Check Porcupine key is valid

### Agent not responding
- Check API key is valid
- Verify network connection
- Look for errors in logs
- Test with simple command first

### Safety validator blocking commands
- Check sensor readings: `check_sensors` tool
- Verify battery level
- Adjust strict mode if needed (with caution!)

## Development

### Adding New Tools

1. Create tool function in `robot_tools.py`:
```python
def my_new_tool(self) -> ToolDefinition:
    async def my_function(param: str) -> Dict[str, Any]:
        # Implementation
        return {
            "type": "tool_result",
            "content": [{"type": "text", "text": "Result"}],
            "is_error": False,
        }

    return ToolDefinition(
        name="my_tool",
        description="What it does",
        input_schema={
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "..."}
            },
            "required": ["param"],
        },
        function=my_function
    )
```

2. Add to `get_all_tools()` method

3. Test it!

### Extending Voice Pipeline

Modify `voice_pipeline.py` to add:
- Custom audio processing
- Additional event handlers
- Integration with other services

## API Routes

The agent is exposed via FastAPI routes in `backend/api/routes/agent.py`:

- `POST /api/v1/agent/command` - Process text command
- `GET /api/v1/agent/status` - Get agent status
- `GET /api/v1/agent/conversation` - Get conversation history
- `DELETE /api/v1/agent/conversation` - Clear conversation
- `GET /api/v1/agent/pipeline/stats` - Get pipeline stats
- `GET /api/v1/agent/health` - Health check

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                               │
│              Voice: "Hey Dash, move forward"                     │
│              Text: API call / Interactive prompt                 │
└───────────────────────┬─────────────────────────────────────────┘
                        │
            ┌───────────▼──────────┐
            │  Wake Word Detector  │
            │   (Porcupine)        │
            └───────────┬──────────┘
                        │
            ┌───────────▼──────────┐
            │  Voice Service (STT) │
            │   (Deepgram)         │
            └───────────┬──────────┘
                        │
        ┌───────────────▼────────────────┐
        │  Claude Agent Service          │
        │  - Natural language processing │
        │  - Tool orchestration          │
        │  - Multi-step reasoning        │
        └───────────┬────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  Robot Tools           │
        │  - Movement            │
        │  - Sensors             │
        │  - Lights, head, sound │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │  Safety Validator      │
        │  - Check obstacles     │
        │  - Verify battery      │
        │  - Enforce limits      │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │  Robot Service         │
        │  (WonderPy)            │
        │  - Bluetooth LE        │
        │  - Hardware control    │
        └───────────┬────────────┘
                    │
┌───────────────────▼─────────────────────┐
│         DASH ROBOT                      │
│  Movement │ Sensors │ Lights │ Speaker  │
└─────────────────────────────────────────┘
```

## License

See main project LICENSE file.
