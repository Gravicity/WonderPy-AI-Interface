# WonderPy AI-Autonomous Robot Platform

An AI-enhanced, voice-controlled interface for WonderWorkshop robots (Dash, Dot, and Cue) powered by Claude Code SDK, Deepgram voice processing, and autonomous agent architecture.

## 🤖 What is This?

This project transforms the original [WonderPy library](https://github.com/playi/WonderPy) into an **autonomous AI-powered robot** with:

- 🎙️ **Voice Control**: "Hey Dash, move forward 5 feet" → Robot understands and acts
- 🧠 **Claude AI Brain**: Natural language understanding with multi-step reasoning
- 🛡️ **Safety First**: Autonomous obstacle detection and validation
- 🔧 **Tool-Based Skills**: Extensible capabilities (movement, sensors, lights, voice)
- 🌐 **Web API**: RESTful control and monitoring
- 📊 **Real-Time Monitoring**: Live sensor data and agent status

**Paradigm Shift**: Instead of programming robot movements, you *talk* to the robot and it autonomously decides how to accomplish tasks safely.

---

## 🚀 Quick Start

### Prerequisites

- **Raspberry Pi 4** (2GB+ RAM recommended, 4GB ideal)
- **Dash/Dot/Cue Robot** from WonderWorkshop
- **Python 3.10+**
- **API Keys**:
  - [Anthropic API key](https://console.anthropic.com/) (Claude Sonnet 4.5)
  - [Deepgram API key](https://deepgram.com/) (for voice features)
  - [Picovoice Porcupine key](https://picovoice.ai/) (for wake word detection)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/WonderPy-AI-Interface.git
cd WonderPy-AI-Interface

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

### Test Without Hardware (Interactive Mode)

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run in interactive text mode (uses mock robot)
python -m backend.services.agent_daemon --mode text

# Try commands:
You: move forward 5 feet
Dash: Okay! Let me check for obstacles first... All clear! I'll move forward 5 feet. [moves] Done!

You: turn around
Dash: Sure! I'll turn 180 degrees. [turns] I've turned around!

You: what's your battery?
Dash: My battery is at 85% - plenty of power!

You: quit
```

### Run with Real Robot

```bash
# Connect Dash to Raspberry Pi via Bluetooth
# Make sure robot is powered on and in range

# Set API keys
export ANTHROPIC_API_KEY="your-key"
export DEEPGRAM_API_KEY="your-key"
export PORCUPINE_ACCESS_KEY="your-key"

# Run voice mode
python -m backend.services.agent_daemon --mode voice

# Say: "Hey Dash, move forward 5 feet"
# Robot will respond and execute!
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VOICE INPUT                              │
│              User: "Hey Dash, move forward 5 feet"               │
└───────────────────────┬─────────────────────────────────────────┘
                        │
            ┌───────────▼──────────┐
            │  Wake Word Detector  │  Porcupine (on-device)
            │   "Hey Dash"         │  ~5% CPU, no latency
            └───────────┬──────────┘
                        │
            ┌───────────▼──────────┐
            │  Speech-to-Text      │  Deepgram Flux
            │  (Deepgram API)      │  $0.0077/min streaming
            └───────────┬──────────┘
                        │
        ┌───────────────▼────────────────┐
        │  Claude Agent (Sonnet 4.5)    │  Autonomous reasoning
        │  - Understands intent          │  - Tool orchestration
        │  - Multi-step planning         │  - Safety validation
        │  - Tool execution              │  - Context retention
        └───────────┬────────────────────┘
                    │
        ┌───────────▼────────────┐
        │  Robot Tools           │  10 core capabilities:
        │  ├─ move_forward       │  - Movement control
        │  ├─ turn               │  - Sensor reading
        │  ├─ check_sensors      │  - Light/head/sound
        │  ├─ set_lights         │  - Speech output
        │  └─ speak              │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │  Safety Validator      │  Multi-tier checks:
        │  - Obstacle detection  │  - 10cm minimum clearance
        │  - Battery monitoring  │  - 15% minimum charge
        │  - Limit enforcement   │  - Speed/distance limits
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │  WonderPy Service      │  Bluetooth LE control
        │  (Hardware Layer)      │  - Real-time commands
        └───────────┬────────────┘
                    │
┌───────────────────▼─────────────────────┐
│         DASH ROBOT (Hardware)           │
│  Movement │ Sensors │ Lights │ Speaker  │
└─────────────────────────────────────────┘
```

---

## ✨ Features

### 🧠 Autonomous AI Agent
- **Natural Language Understanding**: Talk to your robot like a person
- **Multi-Step Reasoning**: "Move forward 5 feet" → Check sensors → Convert units → Move → Confirm
- **Safety-Conscious**: Always checks for obstacles before moving
- **Context Retention**: Remembers conversation and learns preferences

### 🎙️ Voice Interaction
- **Wake Word**: "Hey Dash" activates the robot (using Porcupine)
- **Real-Time STT**: Deepgram Flux model, $0.0077/min
- **Natural TTS**: Deepgram Aura-2, sub-200ms latency
- **Continuous Loop**: Always listening, ready to help

### 🛡️ Safety Features
- **Obstacle Detection**: Won't move if obstacle within 10cm
- **Battery Monitoring**: Warns at 20%, stops movement at 15%
- **Speed Limits**: Max 50cm/s movement, 180°/s turns
- **Emergency Stop**: Immediate halt on command or error
- **Validation Layers**: Hardware limits + sensors + battery + LLM reasoning

### 🔧 10 Core Robot Tools
1. **move_forward** - Move with automatic safety checks
2. **move_backward** - Reverse movement
3. **turn** - Rotate (positive = clockwise)
4. **stop** - Emergency stop
5. **check_sensors** - Read distance sensors (front, sides, rear)
6. **get_battery** - Check battery percentage
7. **set_lights** - Change LED colors (10 presets)
8. **move_head** - Pan/tilt head control
9. **play_tone** - Beep sounds (200-2000 Hz)
10. **speak** - Text-to-speech responses

### 🌐 REST API
- `POST /api/v1/agent/command` - Send text commands
- `GET /api/v1/agent/status` - Get agent status
- `GET /api/v1/agent/conversation` - View conversation history
- `DELETE /api/v1/agent/conversation` - Clear context
- `GET /api/v1/agent/health` - Health check

### 🧪 Developer-Friendly
- **Mock Services**: Test without hardware or API keys
- **Interactive Mode**: Type commands for rapid testing
- **Comprehensive Logging**: Debug with detailed logs
- **Type Safety**: Full type hints with Pydantic models

---

## 📁 Project Structure

```
WonderPy-AI-Interface/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI application
│   │   └── routes/
│   │       ├── agent.py         # Agent control endpoints
│   │       └── robot.py         # Robot control endpoints
│   ├── services/
│   │   ├── README.md            # Detailed service documentation
│   │   ├── robot_service.py     # Hardware abstraction (real + mock)
│   │   ├── safety_validator.py  # Multi-tier safety checks
│   │   ├── robot_tools.py       # 10 tools for Claude agent
│   │   ├── voice_service.py     # Deepgram STT/TTS
│   │   ├── wake_word_service.py # Porcupine wake word detection
│   │   ├── agent_service.py     # Claude AI agent
│   │   ├── voice_pipeline.py    # Complete voice-to-action pipeline
│   │   └── agent_daemon.py      # Standalone service runner
│   ├── utils/
│   │   ├── config.py            # Configuration management
│   │   └── logger.py            # Logging setup
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variables template
├── frontend/                    # (Future: React monitoring dashboard)
├── docker/                      # Docker configuration
├── docs/
│   ├── DEEPGRAM_INTEGRATION.md  # Deepgram implementation guide
│   ├── CLAUDE_SDK_INTEGRATION.md # Claude agent architecture
│   └── ARCHITECTURE_ROADMAP.md  # Complete development roadmap
├── WonderPy/                    # Original WonderPy library
└── README.md                    # This file
```

---

## 🎯 Usage Examples

### Example 1: Simple Movement

```
You: "Hey Dash, move forward 1 meter"

Dash: "Okay! Let me check for obstacles first..."
      [Calls check_sensors tool]
      "All clear! I'll move forward 1 meter. That's 100 centimeters."
      [Calls move_forward tool with distance_cm=100]
      [Moves]
      "Done! I've moved 1 meter forward."
```

### Example 2: Obstacle Avoidance

```
You: "Hey Dash, go forward"

Dash: [Calls check_sensors tool]
      "Oops! I can't move forward - there's something only 8 centimeters
      in front of me. That's too close for safety. Would you like me to
      turn first, or should I try moving backward?"
```

### Example 3: Multi-Step Task

```
You: "Hey Dash, turn around and check what's behind you"

Dash: "Sure! I'll turn 180 degrees."
      [Calls turn tool with degrees=180]
      "I've turned around! Now let me check my sensors..."
      [Calls check_sensors tool]
      "I can see about 45 centimeters behind me - the path looks clear!"
```

### Example 4: API Usage

```bash
# Send command via API
curl -X POST http://localhost:8000/api/v1/agent/command \
  -H "Content-Type: application/json" \
  -d '{"command": "move forward 5 feet", "speak_response": false}'

# Response:
{
  "success": true,
  "response": "Okay! Let me check for obstacles first... All clear! Moving forward 152.4cm... Done!",
  "command": "move forward 5 feet",
  "timestamp": "2025-11-08T14:30:00"
}
```

---

## 🧪 Testing

### Testing Modes

1. **Mock Mode** (No hardware/API keys needed):
   ```bash
   python -m backend.services.agent_daemon --mode text
   ```
   - Uses mock robot service
   - Uses mock voice service
   - Uses mock wake word detector
   - Claude agent requires real API key

2. **Partial Mode** (Mix of real/mock):
   ```python
   pipeline = await create_simple_pipeline(
       api_keys={"anthropic_api_key": "real-key"},
       use_mock_robot=True,    # Mock robot
       use_mock_voice=False    # Real Deepgram
   )
   ```

3. **Production Mode** (All real):
   ```bash
   python -m backend.services.agent_daemon --mode voice
   ```

### Test Checklist

- [ ] Text mode works with mock robot
- [ ] Agent processes natural language correctly
- [ ] Safety validator prevents unsafe commands
- [ ] Tools execute with proper validation
- [ ] Unit conversion works (feet → cm)
- [ ] Multi-step commands work
- [ ] API endpoints respond correctly
- [ ] Real robot connects via Bluetooth
- [ ] Movement commands execute on hardware
- [ ] Sensors read correctly
- [ ] Obstacle detection prevents collisions
- [ ] Battery warnings work
- [ ] Lights/head/sound control works
- [ ] Voice STT transcribes accurately
- [ ] Wake word detection triggers
- [ ] TTS speaks responses
- [ ] Full voice loop completes

---

## 💰 Cost Breakdown

### API Costs (Typical Usage: 30 min/day)

**Claude API (Sonnet 4.5)**:
- Input: ~100K tokens/day = 3M tokens/month
- Output: ~20K tokens/day = 600K tokens/month
- Cost: (3M × $3/M) + (600K × $15/M) = **$18/month**

**Deepgram**:
- STT: 30 min/day × 30 days × $0.0077/min = **$6.93/month**
- TTS: ~75K characters/month × $0.015/1K = **$1.13/month**

**Porcupine Wake Word**: Free tier (on-device processing)

**Total: ~$26/month** for moderate daily use

### Cost Optimization Tips
- Use shorter system prompts (reduce input tokens)
- Implement caching for repeated contexts
- Local wake word detection (free with Porcupine)
- VAD to minimize STT usage (only send speech, not silence)

---

## 🔧 Configuration

Edit `backend/.env`:

```bash
# Required
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# For voice features (optional for testing)
DEEPGRAM_API_KEY="your-deepgram-api-key"
PORCUPINE_ACCESS_KEY="your-picovoice-access-key"

# Voice configuration
VOICE_MODEL_STT="flux-general-en"  # or "nova-3"
VOICE_MODEL_TTS="aura-asteria-en"  # Friendly female voice
WAKE_WORD="hey dash"
VAD_ENABLED=true

# Robot settings
ROBOT_SCAN_TIMEOUT=20
ROBOT_CONNECTION_TIMEOUT=30
SENSOR_UPDATE_RATE_HZ=30

# Environment
ENVIRONMENT="development"  # or "production"
DEBUG=true
LOG_LEVEL="INFO"
```

---

## 🚀 Deployment

### As Systemd Service (Raspberry Pi)

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

# View logs
sudo journalctl -u dash-agent -f
```

### Docker Deployment

```bash
cd docker
docker-compose up -d
```

---

## 🛠️ Troubleshooting

### Robot Won't Connect
- Check Bluetooth: `sudo systemctl status bluetooth`
- Power on robot and ensure it's in range
- Scan for devices: `sudo hcitool scan`
- Verify WonderPy installed: `pip show WonderPy`

### Voice Features Not Working
- Verify API keys are set: `echo $DEEPGRAM_API_KEY`
- Check microphone: `arecord -l`
- Check speaker: `aplay -l`
- Test with mock services first

### Agent Not Responding
- Verify Anthropic API key is valid
- Check network connection
- Look for errors in logs
- Test with simple command: "check sensors"

### Safety Blocking Commands
- Check sensor readings with `check_sensors`
- Verify battery level with `get_battery`
- Review safety thresholds in `safety_validator.py`

---

## 📚 Documentation

- **[Services README](backend/services/README.md)** - Detailed service documentation
- **[Deepgram Integration](docs/DEEPGRAM_INTEGRATION.md)** - Voice processing guide
- **[Claude SDK Integration](docs/CLAUDE_SDK_INTEGRATION.md)** - Agent architecture
- **[Architecture Roadmap](docs/ARCHITECTURE_ROADMAP.md)** - Complete development plan
- **[Original WonderPy Docs](https://github.com/playi/WonderPy)** - Hardware reference

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- 🎨 **Web Dashboard**: React monitoring UI
- 🔌 **Extended Tools**: Weather, smart home, memory/RAG
- 🌍 **Multi-Language**: Support for other languages
- 🤖 **Multi-Robot**: Control multiple robots
- 📊 **Analytics**: Usage tracking and insights
- 🎮 **Game Integration**: Interactive robot games
- 🏫 **Educational**: Curriculum and lesson plans

Please check the [issues](https://github.com/yourusername/WonderPy-AI-Interface/issues) and submit pull requests!

---

## 📝 License

This project builds upon the original [WonderPy library](https://github.com/playi/WonderPy) and maintains the same open-source license.

---

## 🙏 Credits

- **WonderPy**: Original library by [Play-i/WonderWorkshop](https://github.com/playi/WonderPy)
- **Claude**: AI by [Anthropic](https://www.anthropic.com/)
- **Deepgram**: Voice processing by [Deepgram](https://deepgram.com/)
- **Porcupine**: Wake word detection by [Picovoice](https://picovoice.ai/)

---

## 📧 Contact

Questions? Issues? Ideas?

- **Issues**: [GitHub Issues](https://github.com/yourusername/WonderPy-AI-Interface/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/WonderPy-AI-Interface/discussions)

Made something cool? Share your videos and photos! We'd love to see what you build.

---

**Built with ❤️ for robotics education and AI exploration**
