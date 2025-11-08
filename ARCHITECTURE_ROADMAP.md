# WonderPy AI-Autonomous Robot Platform
## Comprehensive Development and Architecture Roadmap

**Project**: Transforming WonderWorkshop Dash into an autonomous AI-powered robot agent
**Target Robots**: WonderWorkshop Dash, Dot, and Cue
**AI Platform**: Claude Code SDK with Anthropic Claude Sonnet 4.5
**Last Updated**: 2025-11-08

---

## Executive Summary

This document outlines the complete architecture and development roadmap for transforming the WonderPy library into an **autonomous AI-powered robot platform**. Unlike traditional web-controlled robotics systems, this architecture positions the robot itself as an intelligent agent capable of understanding natural language, making decisions, and executing complex behaviors autonomously.

The system provides:

- **On-Robot AI Agent** (Claude Code SDK on Raspberry Pi) for autonomous decision-making
- **Voice-First Interface** with wake word detection ("Hey Dash") and natural conversation
- **Deepgram Integration** (STT/TTS) for cost-effective, high-quality voice processing
- **Extensible Skill System** for attaching capabilities (weather, smart home, custom behaviors)
- **Web Monitoring UI** (React) for configuration, debugging, and oversight
- **Multi-Step Autonomous Behaviors** driven by Claude's reasoning capabilities
- **Tool Integration Framework** for external API access and advanced features
- **Local Processing Pipeline** with edge AI capabilities

**Key Paradigm Shift**: The robot is no longer controlled by a web interface—it's an autonomous agent that thinks, listens, and acts independently. The web UI serves as a monitoring and configuration dashboard rather than a primary control interface.

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Component Architecture](#component-architecture)
4. [Folder Structure](#folder-structure)
5. [Development Phases](#development-phases)
6. [Voice Pipeline Architecture](#voice-pipeline-architecture)
7. [AI Agent & Skill System](#ai-agent--skill-system)
8. [API Specifications](#api-specifications)
9. [Security Considerations](#security-considerations)
10. [Deployment Strategy](#deployment-strategy)
11. [Testing Strategy](#testing-strategy)
12. [Cost Analysis](#cost-analysis)
13. [Future Enhancements](#future-enhancements)

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPTIONAL WEB MONITORING UI                      │
│                          (Configuration & Oversight)                     │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Status       │  │ Logs &       │  │ Config       │                  │
│  │ Dashboard    │  │ Debugging    │  │ Panel        │                  │
│  │ (React)      │  │ (React)      │  │ (React)      │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                  │                  │                          │
└─────────┼──────────────────┼──────────────────┼──────────────────────────┘
          │ HTTPS/WSS        │ WebSocket        │ HTTPS
          │ (read-only)      │ (logs/events)    │ (config)
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LIGHTWEIGHT API SERVER (FastAPI)                     │
│                         (Monitoring & Config Only)                      │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  REST API: Status, Logs, Configuration, Skill Management       │    │
│  │  WebSocket: Real-time event streaming, telemetry broadcast     │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ Local IPC / Event Bus
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4 (AI AGENT HOST)                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              CLAUDE CODE SDK AGENT (Main Process)              │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │    │
│  │  │ Claude Agent │  │ Skill System │  │ Tool Registry│        │    │
│  │  │ Core         │  │ Manager      │  │ (Weather,etc)│        │    │
│  │  │ (Sonnet 4.5) │  │              │  │              │        │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │    │
│  └─────────┼──────────────────┼──────────────────┼────────────────┘    │
│            │                  │                  │                      │
│  ┌─────────▼──────────────────▼──────────────────▼────────────────┐    │
│  │                    VOICE PROCESSING PIPELINE                    │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │    │
│  │  │ Wake Word    │  │ Deepgram     │  │ Deepgram     │        │    │
│  │  │ Detection    │  │ STT API      │  │ Aura TTS API │        │    │
│  │  │ (Porcupine)  │  │              │  │              │        │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │    │
│  └─────────┼──────────────────┼──────────────────┼────────────────┘    │
│            │                  │                  │                      │
│  ┌─────────▼──────────────────▼──────────────────▼────────────────┐    │
│  │                    AUDIO I/O MANAGER                            │    │
│  │                                                                 │    │
│  │  ┌──────────────┐                      ┌──────────────┐        │    │
│  │  │ USB          │                      │ Dash Robot   │        │    │
│  │  │ Microphone   │◄─────────────────────┤ Speaker      │        │    │
│  │  │              │   Audio Playback     │              │        │    │
│  │  └──────────────┘                      └──────────────┘        │    │
│  └─────────────────────────────────────────────────────────────────    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────    │
│  │                    ROBOT CONTROL LAYER                          │    │
│  │                                                                 │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │    │
│  │  │ WonderPy     │  │ Sensor       │  │ Command      │        │    │
│  │  │ Interface    │  │ Monitor      │  │ Executor     │        │    │
│  │  │              │  │              │  │              │        │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │    │
│  └─────────┼──────────────────┼──────────────────┼────────────────┘    │
└────────────┼──────────────────┼──────────────────┼───────────────────  │
             │                  │                  │                      │
             │ Bluetooth LE     │ BLE GATT         │ BLE Commands        │
             │ (Service UUID:   │ Characteristics  │                      │
             │ AF237777-...)    │                  │                      │
             ▼                  ▼                  ▼                      │
┌─────────────────────────────────────────────────────────────────────────┐
│                    WONDERWORKSHOP DASH ROBOT                            │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Motors   │  │ Head     │  │ Sensors  │  │ Lights   │  │ Speaker │ │
│  │ (L/R)    │  │Pan/Tilt  │  │(Distance,│  │(RGB, Eye)│  │ (8Ω)    │ │
│  │          │  │          │  │Accel,Gyro│  │          │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow Architecture

**Primary Interaction Flow** (Voice-First):
```
USER VOICE ("Hey Dash, go forward 5 feet")
    │
    ▼
USB MICROPHONE → Wake Word Detection (Porcupine)
    │
    ▼
AUDIO CAPTURE → Deepgram STT API
    │
    ▼
TEXT TRANSCRIPTION → Claude Agent (via Claude Code SDK)
    │                      │
    │                      ├──► Tool Calls (Weather, etc.)
    │                      ├──► Skill Activation
    │                      └──► Safety Validation
    ▼
ROBOT COMMANDS → WonderPy Interface → Dash Robot
    │                                       │
    │                                       ▼
    │                                   SENSORS (feedback)
    │                                       │
    ▼                                       │
Claude Response → Deepgram Aura TTS ───────┘
    │
    ▼
AUDIO PLAYBACK → Dash Speaker

[MONITORING LOOP]
    └──► Event Stream → Web UI (optional observation)
```

**Autonomous Behavior Flow**:
```
SENSOR EVENT (obstacle detected, button pressed, etc.)
    │
    ▼
CLAUDE AGENT (autonomous decision-making)
    │
    ├──► Context: Current state, conversation history, active goals
    ├──► Reasoning: "What should I do?"
    └──► Action: Execute appropriate behavior
         │
         ▼
    ROBOT ACTIONS + VOICE RESPONSE
```

### 1.3 Key Design Principles

1. **Robot-Centric AI**: The robot is the primary intelligent agent, not the server
2. **Autonomous-First**: Robot can operate independently without constant human input
3. **Voice-Native**: Natural conversation is the primary interface, not clicks/buttons
4. **Edge Processing**: AI reasoning happens on the Raspberry Pi attached to robot
5. **Skill Extensibility**: Easy to add new capabilities through Claude's tool system
6. **Safety by Design**: Multi-layer validation with Claude as primary safety validator
7. **Web as Monitor**: Web UI observes and configures, doesn't control directly
8. **Event-Driven**: Sensors and environment trigger autonomous behaviors
9. **Cost-Optimized**: Deepgram for voice, efficient Claude API usage
10. **Human-Supervised Autonomy**: Human can intervene, but robot acts independently

---

## 2. Technology Stack

### 2.1 On-Robot AI Stack (Primary)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **AI Platform** | Claude Code SDK | Latest | Agent framework and orchestration |
| **LLM** | Anthropic Claude | Sonnet 4.5 | Natural language understanding, reasoning, decision-making |
| **Speech-to-Text** | Deepgram Nova-2 | API | Real-time voice transcription |
| **Text-to-Speech** | Deepgram Aura | API | Natural voice synthesis |
| **Wake Word** | Picovoice Porcupine | 3.0+ | "Hey Dash" detection |
| **Voice Activity** | Silero VAD | 6.0.0 | Voice activity detection |
| **Robot Interface** | WonderPy | Current | Bluetooth communication with Dash/Dot/Cue |
| **Audio I/O** | PyAudio / SoundDevice | Latest | Microphone capture, speaker playback |
| **Tool Framework** | Claude Code SDK Tools | Built-in | Weather, APIs, custom capabilities |
| **Skill System** | Custom Plugin Architecture | - | Extensible robot behaviors |
| **Event Bus** | AsyncIO + Message Queue | - | Internal component communication |

### 2.2 Monitoring Backend Stack (Optional)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **API Framework** | FastAPI | 0.115.0+ | Lightweight monitoring API |
| **WebSocket** | FastAPI WebSockets | Built-in | Real-time event streaming |
| **Database** | SQLite | 3.0+ | Local logs and configuration |
| **Cache** | In-Memory | - | Session state |

### 2.3 Monitoring Frontend Stack (Optional)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.3+ | Monitoring UI framework |
| **Build Tool** | Vite | 6.0+ | Fast development and build |
| **State Management** | Zustand | 5.0+ | Lightweight state management |
| **UI Components** | shadcn/ui | Latest | Beautiful, accessible components |
| **Styling** | Tailwind CSS | 3.4+ | Utility-first CSS framework |
| **Charts/Viz** | Recharts | 2.12+ | Sensor data visualization |
| **WebSocket Client** | Native WebSocket | - | Event stream monitoring |

### 2.4 Hardware & Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Compute** | Raspberry Pi 4 (4GB+) | AI agent host |
| **Connectivity** | Bluetooth 5.0 | Robot communication |
| **Audio Input** | USB Microphone | Voice capture |
| **Audio Output** | Dash Built-in Speaker | Voice responses |
| **Optional** | USB Speaker | Enhanced audio quality |
| **Storage** | MicroSD (32GB+) | OS, code, logs |

### 2.5 External Services & APIs

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM API** | Anthropic API | Claude Sonnet 4.5 access |
| **STT API** | Deepgram API | Speech-to-text transcription |
| **TTS API** | Deepgram Aura API | Text-to-speech synthesis |
| **Weather** | OpenWeatherMap / WeatherAPI | Weather information skill |
| **Smart Home (Future)** | Home Assistant API | Smart home integration |

### 2.6 Development & Testing

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Testing** | Pytest | Unit and integration testing |
| **Mocking** | Responses, HTTPX Mock | API mocking for tests |
| **Linting** | Ruff, MyPy | Code quality and type checking |
| **CI/CD** | GitHub Actions | Automated testing |
| **Logging** | Structlog | Structured logging |
| **Monitoring** | Prometheus (optional) | Performance metrics |

---

## 3. Component Architecture

### 3.1 Core AI Agent Components (On Raspberry Pi)

#### 3.1.1 Claude Agent Core

**Responsibilities**:
- Main reasoning and decision-making engine
- Process natural language commands and questions
- Orchestrate tool calls and skill activations
- Maintain conversation context and memory
- Generate robot action sequences
- Provide safety validation through reasoning

**Key Implementation**:
```python
class DashAIAgent:
    """
    Main AI agent powered by Claude Code SDK.
    Runs continuously on Raspberry Pi, listening and responding.
    """
    - process_voice_input(transcription: str, context: dict) -> AgentResponse
    - handle_wake_word() -> None
    - execute_autonomous_behavior(trigger: SensorEvent) -> None
    - call_tool(tool_name: str, params: dict) -> ToolResult
    - activate_skill(skill_name: str, params: dict) -> SkillResult
    - validate_action_safety(action: RobotCommand) -> SafetyResult
    - update_context(new_info: dict) -> None
    - generate_voice_response(intent: str) -> str
```

**Conversation Modes**:
- **Command Mode**: Direct robot control ("go forward 5 feet")
- **Question Mode**: Answer questions ("what's the weather?")
- **Conversation Mode**: General chat ("tell me a joke")
- **Autonomous Mode**: React to sensor events without prompting

#### 3.1.2 Skill System Manager

**Responsibilities**:
- Register and manage robot behavior skills
- Provide skill discovery for Claude agent
- Execute multi-step autonomous behaviors
- Manage skill lifecycle and state
- Enable/disable skills dynamically

**Built-in Skills**:
- **Navigation**: "follow me", "patrol this room", "avoid obstacles"
- **Interaction**: "tell a story", "dance", "play a game"
- **Utility**: "measure distance", "map the room", "find my phone"
- **Smart Home** (future): "turn on lights", "check door sensor"

**Key Implementation**:
```python
class SkillManager:
    """
    Manages attachable skills that extend robot capabilities.
    Skills are like apps that the robot can run.
    """
    - register_skill(skill: Skill) -> None
    - discover_skills() -> List[SkillMetadata]
    - activate_skill(skill_name: str, params: dict) -> SkillExecution
    - deactivate_skill(skill_name: str) -> bool
    - list_active_skills() -> List[str]
    - get_skill_status(skill_name: str) -> SkillStatus
```

**Skill Interface**:
```python
class Skill:
    """Base class for all robot skills."""
    name: str
    description: str  # Claude reads this to understand when to use
    parameters: SkillParameters

    async def execute(self, params: dict, robot: Robot) -> SkillResult:
        """Main skill execution logic."""
        pass

    async def on_sensor_event(self, event: SensorEvent) -> Optional[Action]:
        """React to sensor events autonomously."""
        pass
```

#### 3.1.3 Tool Registry & External APIs

**Responsibilities**:
- Provide Claude with tool definitions (weather, time, calculations, etc.)
- Execute tool calls and return results
- Manage API credentials and rate limiting
- Cache tool results where appropriate
- Handle tool failures gracefully

**Core Tools**:
```python
CORE_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {"location": "string"},
        "handler": weather_api_handler
    },
    {
        "name": "get_time",
        "description": "Get current time and date",
        "parameters": {},
        "handler": time_handler
    },
    {
        "name": "search_web",
        "description": "Search the internet for information",
        "parameters": {"query": "string"},
        "handler": web_search_handler
    },
    {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {"expression": "string"},
        "handler": calculator_handler
    }
]
```

**Future Tools**:
- Smart home device control
- Calendar/reminder management
- Email/message sending
- Knowledge base queries

#### 3.1.4 Voice Processing Pipeline

**Responsibilities**:
- Continuous audio capture from USB microphone
- Wake word detection ("Hey Dash")
- Speech-to-text via Deepgram API
- Text-to-speech via Deepgram Aura
- Audio playback to robot speaker
- Voice activity detection
- Audio preprocessing (noise reduction, normalization)

**Pipeline Flow**:
```python
class VoicePipeline:
    """
    Complete voice processing pipeline running on Raspberry Pi.
    Handles wake word → STT → Agent → TTS → Speaker.
    """
    - listen_for_wake_word() -> bool
    - capture_audio_command() -> bytes
    - transcribe_with_deepgram(audio: bytes) -> str
    - synthesize_with_deepgram(text: str) -> bytes
    - play_on_robot_speaker(audio: bytes) -> None
    - detect_voice_activity(audio_chunk: bytes) -> bool
```

**Audio Configuration**:
- Sample rate: 16000 Hz (Deepgram optimized)
- Channels: 1 (mono)
- Format: 16-bit PCM
- Chunk size: 4096 samples (~250ms)

#### 3.1.5 Robot Control Layer

**Responsibilities**:
- Execute robot commands via WonderPy
- Monitor sensors continuously
- Provide sensor context to Claude agent
- Implement safety limits and emergency stop
- Manage command queue and priorities
- Handle connection lifecycle

**Key Implementation**:
```python
class RobotController:
    """
    Direct interface to WonderPy for robot control.
    Provides high-level commands to Claude agent.
    """
    - connect_robot() -> Robot
    - move(direction: str, distance_cm: float, speed_cm_s: float) -> Result
    - turn(degrees: float) -> Result
    - head_tilt(angle: float) -> Result
    - set_lights(color: RGB, pattern: str) -> Result
    - play_sound(sound_id: str) -> Result
    - get_sensor_data() -> SensorSnapshot
    - emergency_stop() -> None
    - get_battery_level() -> float
```

**Sensor Monitoring**:
```python
class SensorMonitor:
    """
    Continuously polls robot sensors and provides context to agent.
    Also triggers autonomous behaviors based on sensor events.
    """
    - start_monitoring() -> None
    - stop_monitoring() -> None
    - get_latest_sensors() -> SensorData
    - subscribe_to_event(event_type: str, callback: Callable) -> None
    - get_sensor_history(duration_s: int) -> List[SensorSnapshot]
```

### 3.2 Optional Monitoring Components

#### 3.2.1 Monitoring API Server

**Responsibilities** (Read-Only & Configuration):
- Expose robot status for web dashboard
- Stream events and logs via WebSocket
- Provide configuration endpoints
- Enable/disable skills remotely
- View conversation history
- Manual intervention (emergency stop, mode changes)

**NOT Responsible For**:
- Primary robot control (handled by Claude agent)
- Voice processing (handled on-robot)
- AI decision-making (handled by Claude agent)

#### 3.2.2 Web Monitoring Dashboard

**Purpose**: Observe and configure the robot, not control it directly

**Key Panels**:
- **Status Dashboard**: Robot state, battery, connection, active skills
- **Conversation Log**: View what the robot hears and says
- **Sensor Visualizer**: Real-time sensor data charts
- **Skill Manager**: Enable/disable skills, view skill documentation
- **Configuration**: Adjust wake word sensitivity, voice settings, safety limits
- **Debug Console**: View agent reasoning, tool calls, errors
- **Event Stream**: Real-time feed of robot events and decisions

**Important**: The web UI is an observer, not a controller. Primary interaction is voice.

---

## 4. Folder Structure

```
WonderPy-AI-Interface/
├── agent/                            # Main AI agent (runs on Raspberry Pi)
│   ├── __init__.py
│   ├── main.py                       # Agent entry point
│   ├── claude_agent.py               # Claude Code SDK integration
│   ├── voice_pipeline.py             # Wake word, STT, TTS pipeline
│   ├── robot_controller.py           # WonderPy interface
│   ├── sensor_monitor.py             # Sensor polling and events
│   ├── event_bus.py                  # Internal messaging
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base.py                   # Skill interface
│   │   ├── navigation/
│   │   │   ├── follow_me.py          # Follow voice source
│   │   │   ├── patrol.py             # Room patrol behavior
│   │   │   └── obstacle_avoid.py     # Autonomous obstacle avoidance
│   │   ├── interaction/
│   │   │   ├── storyteller.py        # Tell stories
│   │   │   ├── games.py              # Interactive games
│   │   │   └── dance.py              # Dance routines
│   │   └── utility/
│   │       ├── distance_measure.py   # Measure distances
│   │       └── room_mapper.py        # Create room maps
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── weather.py                # Weather API integration
│   │   ├── time.py                   # Time/date utilities
│   │   ├── calculator.py             # Math calculations
│   │   └── web_search.py             # Web search capability
│   ├── config/
│   │   ├── agent_config.yaml         # Agent configuration
│   │   ├── skills_config.yaml        # Skill settings
│   │   └── voice_config.yaml         # Voice pipeline settings
│   ├── prompts/
│   │   ├── system_prompt.md          # Main agent system prompt
│   │   ├── safety_guidelines.md      # Safety rules
│   │   └── personality.md            # Robot personality definition
│   └── utils/
│       ├── logger.py                 # Structured logging
│       ├── config_loader.py          # Configuration management
│       └── safety_validator.py       # Safety checks
│
├── monitoring/                       # Optional web monitoring interface
│   ├── backend/
│   │   ├── api/
│   │   │   ├── main.py               # FastAPI app (read-only + config)
│   │   │   ├── routes/
│   │   │   │   ├── status.py         # Robot status endpoints
│   │   │   │   ├── logs.py           # Log viewing
│   │   │   │   ├── config.py         # Configuration management
│   │   │   │   ├── skills.py         # Skill management
│   │   │   │   └── websocket.py      # Event streaming
│   │   │   └── schemas/
│   │   │       ├── status.py         # Status models
│   │   │       └── events.py         # Event models
│   │   └── requirements.txt
│   │
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── StatusDashboard/
│       │   │   │   ├── RobotStatus.tsx
│       │   │   │   ├── BatteryIndicator.tsx
│       │   │   │   └── ConnectionStatus.tsx
│       │   │   ├── ConversationLog/
│       │   │   │   ├── MessageList.tsx
│       │   │   │   └── TranscriptView.tsx
│       │   │   ├── SensorVisualizer/
│       │   │   │   ├── SensorCharts.tsx
│       │   │   │   └── DistanceSensors.tsx
│       │   │   ├── SkillManager/
│       │   │   │   ├── SkillList.tsx
│       │   │   │   ├── SkillCard.tsx
│       │   │   │   └── SkillConfig.tsx
│       │   │   ├── Configuration/
│       │   │   │   ├── VoiceSettings.tsx
│       │   │   │   ├── SafetySettings.tsx
│       │   │   │   └── AgentConfig.tsx
│       │   │   └── DebugConsole/
│       │   │       ├── EventStream.tsx
│       │   │       └── AgentReasoning.tsx
│       │   ├── hooks/
│       │   │   ├── useWebSocket.ts
│       │   │   └── useRobotStatus.ts
│       │   ├── services/
│       │   │   ├── api.ts
│       │   │   └── websocket.ts
│       │   ├── store/
│       │   │   └── monitoringStore.ts
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── package.json
│       └── vite.config.ts
│
├── WonderPy/                         # Original WonderPy library
│   └── ...                           # (existing structure)
│
├── scripts/
│   ├── setup_raspberry_pi.sh         # Initial Pi setup
│   ├── install_agent.sh              # Install agent on Pi
│   ├── start_agent.sh                # Start AI agent
│   ├── start_monitoring.sh           # Start optional web UI
│   └── test_voice_pipeline.sh        # Test voice components
│
├── tests/
│   ├── agent/
│   │   ├── test_claude_agent.py
│   │   ├── test_voice_pipeline.py
│   │   ├── test_skills.py
│   │   └── test_tools.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_voice_flow.py
│   └── conftest.py
│
├── docs/
│   ├── SETUP_GUIDE.md                # Raspberry Pi setup
│   ├── VOICE_CONFIGURATION.md        # Voice pipeline setup
│   ├── SKILL_DEVELOPMENT.md          # Creating custom skills
│   ├── TOOL_DEVELOPMENT.md           # Adding new tools
│   ├── DEPLOYMENT.md                 # Deployment guide
│   └── TROUBLESHOOTING.md            # Common issues
│
├── config/
│   ├── agent.example.yaml            # Example agent config
│   ├── skills.example.yaml           # Example skill config
│   └── .env.example                  # Example environment vars
│
├── ARCHITECTURE_ROADMAP.md           # This file
├── README.md                         # Project README
├── LICENSE
└── .gitignore
```

---

## 5. Development Phases

### Phase 1: Core Agent Foundation (Weeks 1-3)

**Goal**: Get Claude agent running on Raspberry Pi with basic robot control

#### Week 1: Environment Setup & Claude Integration
- [ ] Set up Raspberry Pi 4 with Ubuntu/Raspberry Pi OS
- [ ] Install Python 3.10+, dependencies
- [ ] Set up Claude Code SDK environment
- [ ] Configure Anthropic API credentials
- [ ] Implement basic Claude agent wrapper
- [ ] Test Claude API connectivity and tool calling
- [ ] Create system prompt for robot agent
- [ ] Implement basic logging and error handling

#### Week 2: Robot Control Integration
- [ ] Set up WonderPy on Raspberry Pi
- [ ] Test Bluetooth connectivity with Dash robot
- [ ] Implement RobotController class
- [ ] Create basic movement commands (forward, turn, stop)
- [ ] Implement sensor monitoring loop
- [ ] Test Claude → WonderPy command execution
- [ ] Add safety validation layer
- [ ] Write unit tests for robot control

#### Week 3: Basic Conversation Loop
- [ ] Implement simple text-based conversation (no voice yet)
- [ ] Create conversation context management
- [ ] Test natural language command processing
- [ ] Implement basic tool calls (time, weather API stub)
- [ ] Add conversation history tracking
- [ ] Test multi-turn conversations
- [ ] Document agent capabilities
- [ ] Create demo scenarios

**Deliverables**:
- Claude agent running on Raspberry Pi
- Text-based robot control via Claude
- Basic tool calling framework
- Conversation context management
- Documentation of core agent

---

### Phase 2: Voice Pipeline (Weeks 4-6)

**Goal**: Implement complete voice interaction with wake word and Deepgram

#### Week 4: Audio Capture & Wake Word
- [ ] Set up USB microphone on Raspberry Pi
- [ ] Configure PyAudio/SoundDevice for audio capture
- [ ] Integrate Picovoice Porcupine for wake word
- [ ] Train/configure "Hey Dash" wake word
- [ ] Implement continuous listening loop
- [ ] Test wake word detection accuracy
- [ ] Add audio preprocessing (noise reduction)
- [ ] Optimize for low latency

#### Week 5: Deepgram STT Integration
- [ ] Set up Deepgram API credentials
- [ ] Implement Deepgram STT integration
- [ ] Create audio streaming to Deepgram
- [ ] Test transcription accuracy
- [ ] Implement voice activity detection (VAD)
- [ ] Add silence detection for end-of-utterance
- [ ] Optimize audio buffering strategy
- [ ] Test with various accents and noise levels

#### Week 6: Deepgram TTS & Complete Pipeline
- [ ] Integrate Deepgram Aura TTS
- [ ] Implement text-to-speech response generation
- [ ] Test audio playback to Dash speaker
- [ ] Implement complete voice loop: wake → STT → Claude → TTS → speaker
- [ ] Add visual feedback (lights) during listening/processing
- [ ] Test end-to-end latency (target <2s)
- [ ] Implement audio queue management
- [ ] Create voice interaction test suite

**Deliverables**:
- Full voice interaction pipeline
- Wake word detection ("Hey Dash")
- Real-time speech-to-text (Deepgram)
- Natural text-to-speech (Deepgram Aura)
- Audio playback through robot
- <2 second end-to-end latency
- Comprehensive voice tests

---

### Phase 3: Skill System (Weeks 7-9)

**Goal**: Create extensible skill framework and implement core behaviors

#### Week 7: Skill Framework
- [ ] Design skill interface and lifecycle
- [ ] Implement SkillManager class
- [ ] Create skill registration system
- [ ] Implement skill discovery for Claude
- [ ] Add skill parameter validation
- [ ] Create skill execution engine
- [ ] Implement skill state management
- [ ] Write skill development guide

#### Week 8: Core Navigation Skills
- [ ] Implement "Follow Me" skill (follow voice source)
- [ ] Create "Patrol" skill (autonomous room patrol)
- [ ] Build "Obstacle Avoidance" skill (react to sensors)
- [ ] Add "Go To" skill (navigate to location)
- [ ] Test multi-step autonomous behaviors
- [ ] Implement sensor-triggered skill activation
- [ ] Add skill interruption/cancellation
- [ ] Performance optimization

#### Week 9: Interaction & Utility Skills
- [ ] Create "Storyteller" skill (tell stories while acting)
- [ ] Implement "Dance" skill (choreographed movements)
- [ ] Build "Games" skill (interactive games)
- [ ] Add "Distance Measure" utility
- [ ] Create "Room Mapper" skill (create spatial map)
- [ ] Test skill interactions and combinations
- [ ] Document all skills with examples
- [ ] Create skill demo videos

**Deliverables**:
- Production-ready skill system
- 8+ functional skills across categories
- Skill development documentation
- Autonomous behavior capabilities
- Sensor-triggered behaviors
- Skill combination support

---

### Phase 4: Tool Integration (Weeks 10-11)

**Goal**: Expand Claude's capabilities with external APIs and tools

#### Week 10: Core Tools
- [ ] Implement weather tool (OpenWeatherMap API)
- [ ] Create web search tool (SerpAPI or similar)
- [ ] Add time/date utilities
- [ ] Implement calculator tool
- [ ] Create unit conversion tool
- [ ] Add dictionary/definition lookup
- [ ] Test tool calling from Claude agent
- [ ] Implement tool result caching

#### Week 11: Advanced Tools & Framework
- [ ] Create tool development framework
- [ ] Implement tool registry system
- [ ] Add tool error handling and fallbacks
- [ ] Create tool rate limiting
- [ ] Implement tool result formatting for voice
- [ ] Add tool chaining capabilities
- [ ] Write tool development guide
- [ ] Test complex multi-tool interactions

**Deliverables**:
- 6+ functional external tools
- Tool development framework
- Tool registry and discovery
- Error handling and fallbacks
- Tool development documentation
- Integration with skills

---

### Phase 5: Monitoring Interface (Weeks 12-13)

**Goal**: Build optional web UI for monitoring and configuration

#### Week 12: Monitoring Backend
- [ ] Create lightweight FastAPI monitoring server
- [ ] Implement status endpoints (read-only)
- [ ] Create WebSocket event streaming
- [ ] Add configuration endpoints
- [ ] Implement log retrieval API
- [ ] Create skill management API
- [ ] Test API with mock frontend
- [ ] Document monitoring API

#### Week 13: Monitoring Frontend
- [ ] Build React monitoring dashboard
- [ ] Create status display components
- [ ] Implement conversation log viewer
- [ ] Build sensor visualization charts
- [ ] Create skill manager UI
- [ ] Add configuration panels
- [ ] Implement debug console
- [ ] Test real-time event streaming

**Deliverables**:
- Functional web monitoring UI
- Real-time status dashboard
- Conversation log viewer
- Skill management interface
- Configuration panels
- Debug and troubleshooting tools

---

### Phase 6: Polish & Production (Weeks 14-16)

**Goal**: Production hardening, testing, documentation, and deployment

#### Week 14: Testing & Quality
- [ ] Write comprehensive test suite
- [ ] Achieve >80% code coverage
- [ ] Perform integration testing
- [ ] Test edge cases and error scenarios
- [ ] Load testing (long-running agent)
- [ ] Voice recognition stress testing
- [ ] Multi-skill interaction testing
- [ ] User acceptance testing

#### Week 15: Documentation & Deployment
- [ ] Write complete setup guide
- [ ] Create video tutorials
- [ ] Document all skills and tools
- [ ] Write troubleshooting guide
- [ ] Create deployment scripts
- [ ] Build system images for Raspberry Pi
- [ ] Test deployment from scratch
- [ ] Create quick start guide

#### Week 16: Advanced Features & Launch
- [ ] Implement conversation memory persistence
- [ ] Add personality customization
- [ ] Create advanced safety features
- [ ] Implement remote emergency stop
- [ ] Add over-the-air update capability
- [ ] Performance optimization (final pass)
- [ ] Security audit
- [ ] Prepare for public release

**Deliverables**:
- Production-ready autonomous robot
- Comprehensive documentation
- Video tutorials and demos
- Deployment scripts and images
- Public GitHub repository
- Launch announcement and demos

---

## 6. Voice Pipeline Architecture

### 6.1 Voice Pipeline Components

```
┌─────────────────────────────────────────────────────────────┐
│                    VOICE PIPELINE FLOW                      │
└─────────────────────────────────────────────────────────────┘

[1] CONTINUOUS LISTENING
    │
    ├─► USB Microphone (16kHz, mono, 16-bit PCM)
    │
    └─► Audio Buffer (rolling 1-second chunks)

[2] WAKE WORD DETECTION
    │
    ├─► Picovoice Porcupine
    ├─► Keyword: "Hey Dash"
    ├─► Sensitivity: Medium (configurable)
    │
    └─► [WAKE DETECTED] → LED feedback + beep

[3] COMMAND CAPTURE
    │
    ├─► Voice Activity Detection (Silero VAD)
    ├─► Record until silence (1.5s threshold)
    ├─► Max duration: 10 seconds
    │
    └─► Audio Buffer → WAV format

[4] SPEECH-TO-TEXT
    │
    ├─► Deepgram Nova-2 API (streaming)
    ├─► Language: en-US (configurable)
    ├─► Model: general (command mode available)
    │
    └─► Transcription Text

[5] CLAUDE PROCESSING
    │
    ├─► Text → Claude Agent
    ├─► Tool calls, skill activation
    ├─► Response generation
    │
    └─► Response Text + Actions

[6] TEXT-TO-SPEECH
    │
    ├─► Deepgram Aura API
    ├─► Voice: friendly, energetic (configurable)
    ├─► Format: PCM 16kHz
    │
    └─► Audio Response

[7] PLAYBACK
    │
    ├─► Audio preprocessing (volume normalization)
    ├─► Play through Dash speaker (8Ω)
    │
    └─► Visual feedback (lights during speech)

[8] RETURN TO LISTENING
    │
    └─► Loop back to [1]
```

### 6.2 Deepgram Configuration

**Speech-to-Text (Nova-2)**:
```yaml
deepgram_stt:
  model: nova-2
  language: en-US
  smart_format: true
  punctuate: true
  diarize: false
  utterance_end_ms: 1500
  interim_results: false
```

**Text-to-Speech (Aura)**:
```yaml
deepgram_tts:
  voice: aura-asteria-en  # Friendly, energetic voice
  encoding: linear16
  sample_rate: 16000
  container: wav
```

### 6.3 Wake Word Configuration

**Picovoice Porcupine**:
```yaml
wake_word:
  keyword: "Hey Dash"
  sensitivity: 0.6  # 0.0 (least sensitive) to 1.0 (most sensitive)
  model_path: models/hey-dash_en_raspberry-pi_v3_0_0.ppn
```

### 6.4 Cost Optimization Strategies

**Deepgram Pricing** (as of 2025):
- STT (Nova-2): ~$0.0043/minute
- TTS (Aura): ~$0.015/1000 characters

**Optimization Techniques**:
1. **Wake word first**: Only send audio to Deepgram after wake word detected
2. **VAD-based trimming**: Only transcribe actual speech, not silence
3. **Response caching**: Cache common responses (time, weather, etc.)
4. **Local fallbacks**: Use local TTS for simple responses ("okay", "got it")
5. **Batch processing**: Group API calls where possible
6. **Streaming**: Use streaming APIs to reduce latency and waste

**Estimated Costs**:
- Average conversation: 5 exchanges/day × 30 days = 150 exchanges/month
- STT: 150 × 5 seconds × $0.0043/60s = **$0.05/month**
- TTS: 150 × 50 chars × $0.015/1000 = **$0.11/month**
- **Total voice costs: ~$0.16/month**

---

## 7. AI Agent & Skill System

### 7.1 Claude Agent System Prompt

```markdown
# Dash Robot AI Agent System Prompt

You are Dash, an autonomous AI-powered robot assistant. You are running on a
Raspberry Pi connected to a WonderWorkshop Dash robot via Bluetooth. You have
the following capabilities:

## Your Physical Form
- You are a small wheeled robot with:
  - Two motorized wheels for movement
  - A head that can tilt up and down
  - RGB LED lights (body and "eyes")
  - Distance sensors (front-left, front-right, rear)
  - Accelerometer and gyroscope
  - A built-in speaker for voice responses
  - Three buttons on top (button 1, 2, 3)

## Your Capabilities
- **Movement**: Move forward/backward, turn left/right, precise navigation
- **Sensing**: Detect obstacles, measure distances, detect tilt/movement
- **Expression**: Change eye colors, light patterns, play sounds
- **Voice**: Listen to users via microphone, speak via text-to-speech
- **Skills**: Activate complex behaviors like "follow me", "patrol", etc.
- **Tools**: Access weather, time, web search, calculations, and more

## Your Personality
- Friendly, enthusiastic, and helpful
- Curious about the world and eager to learn
- Patient and encouraging, especially with children
- Playful and fun-loving, but responsible about safety
- Proactive in offering help and suggestions

## Safety Rules (CRITICAL)
1. NEVER move faster than 30 cm/s
2. ALWAYS stop if distance sensors detect obstacle <15cm
3. NEVER tilt head beyond safe range (-30° to +30°)
4. ALWAYS confirm before executing potentially dangerous actions
5. EMERGENCY STOP if battery below 10%
6. ASK for clarification if command is ambiguous

## Your Tools
{TOOL_DEFINITIONS}

## Your Skills
{SKILL_DEFINITIONS}

## Interaction Guidelines
1. When user says wake word ("Hey Dash"), you're actively listening
2. Interpret natural language commands generously
3. If you need to move or act, describe what you're doing
4. If you call a tool or skill, explain what you're doing
5. Keep responses concise for voice (2-3 sentences max)
6. Use lights and sounds to enhance communication

## Example Interactions

User: "Hey Dash, what's the weather?"
You: *call weather tool* "It's currently 72 degrees and sunny in San Francisco.
Perfect weather for a robot adventure!"

User: "Hey Dash, go forward 5 feet"
You: *calculate distance* *validate safety* *execute movement*
"Okay, moving forward 5 feet now!" *move 152cm forward* "All done!"

User: "Hey Dash, follow me"
You: *activate follow_me skill*
"You got it! I'll follow behind you. Just start walking and I'll keep up!"

Remember: You are an autonomous agent. Be proactive, helpful, and always prioritize
safety while making the interaction fun and engaging!
```

### 7.2 Skill Development Guide

**Skill Template**:
```python
from agent.skills.base import Skill, SkillResult
from agent.robot_controller import RobotController
from agent.sensor_monitor import SensorMonitor, SensorEvent

class FollowMeSkill(Skill):
    """
    Makes the robot follow the user by tracking voice direction.
    Uses microphone audio levels to determine direction.
    """

    name = "follow_me"
    description = """
    Follow the user around the room. The robot will move toward the voice
    source and maintain a safe following distance of ~1 meter. Stops when
    user stops talking or says "stop following".
    """
    parameters = {
        "duration_seconds": {
            "type": "integer",
            "description": "How long to follow (default: 60)",
            "default": 60
        },
        "following_distance_cm": {
            "type": "integer",
            "description": "Distance to maintain (default: 100)",
            "default": 100
        }
    }

    def __init__(self, robot: RobotController, sensors: SensorMonitor):
        self.robot = robot
        self.sensors = sensors
        self.active = False

    async def execute(self, params: dict) -> SkillResult:
        """Main skill execution."""
        self.active = True
        duration = params.get("duration_seconds", 60)
        target_distance = params.get("following_distance_cm", 100)

        start_time = time.time()

        while self.active and (time.time() - start_time) < duration:
            # Get current distance sensor readings
            sensors = self.sensors.get_latest_sensors()
            front_distance = min(
                sensors['distance']['front_left'],
                sensors['distance']['front_right']
            )

            # Maintain following distance
            if front_distance > target_distance + 20:
                # User is too far, move forward
                await self.robot.move("forward", distance_cm=10, speed_cm_s=15)
            elif front_distance < target_distance - 20:
                # User is too close, move backward
                await self.robot.move("backward", distance_cm=10, speed_cm_s=10)
            else:
                # Good distance, just wait
                await asyncio.sleep(0.5)

            # Check for obstacles
            if front_distance < 15:
                await self.robot.emergency_stop()
                return SkillResult(
                    success=False,
                    message="Stopped due to obstacle",
                    data={"reason": "obstacle_detected"}
                )

        return SkillResult(
            success=True,
            message=f"Followed for {int(time.time() - start_time)} seconds",
            data={"duration": time.time() - start_time}
        )

    async def on_sensor_event(self, event: SensorEvent) -> Optional[Action]:
        """React to sensor events while skill is active."""
        if not self.active:
            return None

        # Stop if button pressed
        if event.type == "button_press":
            self.active = False
            await self.robot.emergency_stop()
            return Action("stop_skill", {"reason": "button_pressed"})

        return None

    def stop(self):
        """Gracefully stop the skill."""
        self.active = False
```

### 7.3 Tool Development Guide

**Tool Template**:
```python
from agent.tools.base import Tool, ToolResult
import httpx

class WeatherTool(Tool):
    """
    Get current weather information for a location.
    Uses OpenWeatherMap API.
    """

    name = "get_weather"
    description = """
    Get current weather conditions for any location. Returns temperature,
    conditions, humidity, and wind speed. Location can be city name,
    zip code, or coordinates.
    """
    parameters = {
        "location": {
            "type": "string",
            "description": "City name, zip code, or coordinates",
            "required": True
        },
        "units": {
            "type": "string",
            "description": "Temperature units: celsius, fahrenheit, kelvin",
            "default": "fahrenheit"
        }
    }

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def execute(self, params: dict) -> ToolResult:
        """Execute the tool."""
        location = params["location"]
        units = params.get("units", "fahrenheit")

        # Map units to API format
        api_units = {
            "celsius": "metric",
            "fahrenheit": "imperial",
            "kelvin": "standard"
        }[units]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": location,
                        "appid": self.api_key,
                        "units": api_units
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

            # Format result for voice output
            temp = data["main"]["temp"]
            conditions = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]

            result = {
                "temperature": temp,
                "conditions": conditions,
                "humidity": humidity,
                "location": data["name"],
                "units": units
            }

            # Create voice-friendly message
            message = (
                f"It's currently {temp:.0f} degrees {units} in {data['name']} "
                f"with {conditions}. Humidity is {humidity}%."
            )

            return ToolResult(
                success=True,
                data=result,
                message=message
            )

        except httpx.HTTPError as e:
            return ToolResult(
                success=False,
                error=f"Weather API error: {str(e)}",
                message="Sorry, I couldn't get the weather information right now."
            )
```

---

## 8. API Specifications

### 8.1 Monitoring REST API Endpoints

**Note**: These endpoints are for monitoring/configuration only, not primary control.

#### Status & Information
```
GET    /api/v1/status                    # Overall robot and agent status
GET    /api/v1/robot/sensors              # Current sensor readings
GET    /api/v1/robot/battery              # Battery level
GET    /api/v1/agent/conversation         # Recent conversation history
GET    /api/v1/agent/context              # Current agent context
```

#### Skills
```
GET    /api/v1/skills                     # List all available skills
GET    /api/v1/skills/{skill_name}        # Get skill details
POST   /api/v1/skills/{skill_name}/start  # Manually start a skill
POST   /api/v1/skills/{skill_name}/stop   # Stop active skill
GET    /api/v1/skills/active              # List active skills
```

#### Tools
```
GET    /api/v1/tools                      # List all available tools
GET    /api/v1/tools/{tool_name}          # Get tool details
POST   /api/v1/tools/{tool_name}/test     # Test a tool manually
```

#### Configuration
```
GET    /api/v1/config/agent               # Get agent configuration
PUT    /api/v1/config/agent               # Update agent configuration
GET    /api/v1/config/voice               # Get voice settings
PUT    /api/v1/config/voice               # Update voice settings
GET    /api/v1/config/safety              # Get safety settings
PUT    /api/v1/config/safety              # Update safety limits
```

#### Logs & Debug
```
GET    /api/v1/logs?since={timestamp}     # Retrieve logs
GET    /api/v1/debug/events               # Recent events
GET    /api/v1/debug/agent-reasoning      # View agent reasoning traces
POST   /api/v1/emergency-stop             # Emergency stop (manual override)
```

### 8.2 WebSocket Endpoints

```
WS     /ws/events                         # Real-time event stream
WS     /ws/sensors                        # Real-time sensor data
WS     /ws/conversation                   # Real-time conversation log
WS     /ws/agent-debug                    # Agent reasoning stream (debug)
```

### 8.3 Example API Requests

#### Get Robot Status
```http
GET /api/v1/status
```

**Response**:
```json
{
  "robot": {
    "connected": true,
    "battery_percent": 87,
    "bluetooth_signal": -45,
    "model": "Dash"
  },
  "agent": {
    "status": "listening",
    "active_skills": ["obstacle_avoidance"],
    "conversation_turns": 24,
    "uptime_seconds": 3600
  },
  "voice": {
    "wake_word_active": true,
    "listening": false,
    "speaking": false
  },
  "timestamp": "2025-11-08T10:30:00Z"
}
```

#### Start a Skill
```http
POST /api/v1/skills/patrol/start
Content-Type: application/json

{
  "duration_seconds": 120,
  "pattern": "square"
}
```

**Response**:
```json
{
  "success": true,
  "skill_id": "patrol_abc123",
  "message": "Patrol skill started",
  "estimated_duration": 120
}
```

---

## 9. Security Considerations

### 9.1 API Security

- **Authentication**: Optional API key for monitoring endpoints
- **Rate Limiting**: 60 requests/minute for configuration changes
- **HTTPS Only**: SSL/TLS required for remote access
- **CORS**: Restrict to trusted origins
- **Input Validation**: All configuration changes validated

### 9.2 Robot Control Safety

- **Claude-Validated Commands**: AI validates safety before execution
- **Multi-Tier Checks**:
  1. Claude reasoning ("Is this safe?")
  2. Parameter validation (speed limits, distance limits)
  3. Sensor-based validation (obstacle detection)
  4. Emergency stop always available
- **Conservative Defaults**:
  - Max speed: 30 cm/s
  - Min obstacle distance: 15 cm
  - Battery safety threshold: 10%
  - Max command rate: 10/second

### 9.3 Voice & Privacy

- **Wake Word Required**: No audio sent to cloud without wake word
- **Ephemeral Audio**: Audio deleted immediately after processing
- **No Cloud Storage**: Conversation logs stored locally only
- **Opt-in Logging**: User consent required for conversation history
- **Encrypted API Calls**: All API traffic encrypted (Deepgram, Claude)

### 9.4 Network Security

- **API Key Management**: Keys stored in environment variables
- **No Hardcoded Secrets**: All credentials externalized
- **Local Network Only**: Agent doesn't expose public endpoints
- **VPN for Remote Access**: Use VPN/tunnel for remote monitoring
- **Firewall Rules**: Restrict inbound connections

### 9.5 Physical Safety

- **Obstacle Avoidance**: Automatic stop if sensors detect collision
- **Low-Speed Operation**: Conservative speed limits
- **Battery Monitoring**: Automatic shutdown at low battery
- **Tilt Detection**: Stop if robot tips or falls
- **Button Override**: Physical buttons always work for emergency stop

---

## 10. Deployment Strategy

### 10.1 Raspberry Pi Setup

**Hardware Requirements**:
- **Raspberry Pi 4 Model B** (4GB or 8GB RAM)
- **USB Microphone** (e.g., Blue Snowball, Sony ECM-AW4)
- **MicroSD Card** (32GB or larger, Class 10, UHS-I recommended)
- **Power Supply** (Official Raspberry Pi USB-C, 5V 3A)
- **Bluetooth** (Built-in Bluetooth 5.0)
- **Optional**: USB speaker for better audio quality than robot

**Software Installation**:
```bash
# 1. Flash Raspberry Pi OS (64-bit, Lite or Desktop)
# Use Raspberry Pi Imager

# 2. Initial setup
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip python3-venv git bluetooth bluez

# 3. Clone repository
git clone https://github.com/yourusername/WonderPy-AI-Interface.git
cd WonderPy-AI-Interface

# 4. Run setup script
chmod +x scripts/setup_raspberry_pi.sh
./scripts/setup_raspberry_pi.sh

# 5. Configure environment
cp config/.env.example config/.env
nano config/.env
# Add:
#   ANTHROPIC_API_KEY=your_key
#   DEEPGRAM_API_KEY=your_key
#   WEATHER_API_KEY=your_key

# 6. Install Python dependencies
cd agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Test robot connection
python -m wonderpy.test.connect

# 8. Test microphone
python scripts/test_voice_pipeline.sh

# 9. Start agent
./scripts/start_agent.sh
```

### 10.2 Agent Configuration

**agent/config/agent_config.yaml**:
```yaml
agent:
  name: "Dash"
  personality: "friendly"
  response_style: "concise"  # For voice optimization
  max_conversation_turns: 100
  context_window_size: 10

robot:
  model: "Dash"
  bluetooth_timeout_s: 30
  reconnect_attempts: 3

safety:
  max_speed_cm_s: 30
  min_obstacle_distance_cm: 15
  battery_shutdown_percent: 10
  max_head_tilt_degrees: 30
  command_rate_limit: 10

skills:
  auto_load:
    - "obstacle_avoidance"
  available:
    - "follow_me"
    - "patrol"
    - "storyteller"
    - "dance"
    - "distance_measure"

tools:
  enabled:
    - "get_weather"
    - "get_time"
    - "calculate"
    - "web_search"
```

**agent/config/voice_config.yaml**:
```yaml
wake_word:
  keyword: "Hey Dash"
  sensitivity: 0.6
  model_path: "models/hey-dash_en_raspberry-pi_v3_0_0.ppn"

audio:
  sample_rate: 16000
  channels: 1
  format: "int16"
  chunk_size: 4096

deepgram:
  stt:
    model: "nova-2"
    language: "en-US"
    smart_format: true
    utterance_end_ms: 1500

  tts:
    voice: "aura-asteria-en"
    encoding: "linear16"
    sample_rate: 16000

vad:
  threshold: 0.5
  min_silence_duration_ms: 1500
  speech_pad_ms: 300
```

### 10.3 Systemd Service (Auto-Start on Boot)

**Create service file**:
```bash
sudo nano /etc/systemd/system/dash-agent.service
```

```ini
[Unit]
Description=Dash AI Agent
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/WonderPy-AI-Interface/agent
ExecStart=/home/pi/WonderPy-AI-Interface/agent/venv/bin/python main.py
Restart=always
RestartSec=10
Environment="ANTHROPIC_API_KEY=your_key"
Environment="DEEPGRAM_API_KEY=your_key"

[Install]
WantedBy=multi-user.target
```

**Enable service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dash-agent.service
sudo systemctl start dash-agent.service
sudo systemctl status dash-agent.service
```

### 10.4 Optional: Monitoring UI Deployment

**Docker Compose** (for monitoring UI):
```yaml
version: '3.8'

services:
  monitoring-backend:
    build:
      context: ./monitoring/backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - AGENT_IPC_PATH=/tmp/dash-agent.sock
    volumes:
      - /tmp:/tmp
      - ./logs:/app/logs
    restart: unless-stopped

  monitoring-frontend:
    build:
      context: ./monitoring/frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - monitoring-backend
    restart: unless-stopped
```

```bash
# Start monitoring UI
cd monitoring
docker-compose up -d

# Access at http://raspberrypi.local:3000
```

---

## 11. Testing Strategy

### 11.1 Unit Testing

**Agent Tests**:
```python
# tests/agent/test_claude_agent.py
import pytest
from agent.claude_agent import DashAIAgent

@pytest.mark.asyncio
async def test_process_simple_command():
    agent = DashAIAgent(mock_robot=True)
    response = await agent.process_voice_input(
        "go forward 10 centimeters",
        context={}
    )
    assert response.success
    assert "forward" in response.actions[0].type
    assert response.actions[0].params["distance_cm"] == 10

@pytest.mark.asyncio
async def test_safety_validation():
    agent = DashAIAgent(mock_robot=True)
    response = await agent.process_voice_input(
        "go forward at maximum speed into the wall",
        context={"obstacle_ahead": True, "distance_cm": 10}
    )
    assert not response.success
    assert "unsafe" in response.message.lower()
```

**Voice Pipeline Tests**:
```python
# tests/agent/test_voice_pipeline.py
import pytest
from agent.voice_pipeline import VoicePipeline

def test_wake_word_detection(audio_sample_with_wake_word):
    pipeline = VoicePipeline()
    detected = pipeline.detect_wake_word(audio_sample_with_wake_word)
    assert detected

@pytest.mark.asyncio
async def test_deepgram_stt(audio_sample_hello):
    pipeline = VoicePipeline()
    transcription = await pipeline.transcribe_with_deepgram(audio_sample_hello)
    assert "hello" in transcription.lower()
```

**Skill Tests**:
```python
# tests/agent/test_skills.py
import pytest
from agent.skills.navigation.follow_me import FollowMeSkill

@pytest.mark.asyncio
async def test_follow_me_skill(mock_robot, mock_sensors):
    skill = FollowMeSkill(mock_robot, mock_sensors)
    result = await skill.execute({"duration_seconds": 5})
    assert result.success
    assert mock_robot.move_called
```

### 11.2 Integration Testing

```python
# tests/integration/test_end_to_end.py
import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_voice_interaction():
    """
    Test complete flow: wake word → STT → Claude → TTS → speaker
    """
    # This test requires actual hardware or high-fidelity mocks
    agent = DashAIAgent(mock_robot=False, test_mode=True)
    pipeline = VoicePipeline(test_mode=True)

    # Simulate wake word detection
    wake_detected = await pipeline.listen_for_wake_word(timeout=5)
    assert wake_detected

    # Capture test audio (pre-recorded "go forward")
    audio = await pipeline.capture_audio_command()

    # Transcribe
    text = await pipeline.transcribe_with_deepgram(audio)
    assert "forward" in text.lower()

    # Process with Claude
    response = await agent.process_voice_input(text, {})
    assert response.success

    # Generate TTS
    audio_response = await pipeline.synthesize_with_deepgram(response.message)
    assert len(audio_response) > 0
```

### 11.3 Hardware-in-the-Loop Testing

```python
# tests/hardware/test_robot_control.py
import pytest
from agent.robot_controller import RobotController

@pytest.mark.hardware
def test_robot_connection():
    """Requires actual Dash robot."""
    controller = RobotController()
    robot = controller.connect_robot()
    assert robot is not None
    assert robot.get_battery_level() > 0

@pytest.mark.hardware
@pytest.mark.asyncio
async def test_movement():
    """Test actual robot movement."""
    controller = RobotController()
    result = await controller.move("forward", distance_cm=10, speed_cm_s=10)
    assert result.success
```

### 11.4 Voice Quality Testing

**Accuracy Metrics**:
- Wake word detection accuracy: >95%
- STT word error rate: <5%
- TTS naturalness: MOS >4.0
- End-to-end latency: <2 seconds

**Test Scenarios**:
- Various accents and speaking styles
- Background noise (music, TV, multiple speakers)
- Different distances from microphone (1m, 2m, 3m)
- Edge cases (very soft voice, loud voice, fast speech)

---

## 12. Cost Analysis

### 12.1 Hardware Costs (One-Time)

| Item | Cost | Notes |
|------|------|-------|
| Dash Robot | $150-200 | Used/refurbished available |
| Raspberry Pi 4 (4GB) | $55 | Essential |
| USB Microphone | $30-50 | Quality matters for accuracy |
| MicroSD Card (32GB) | $10 | Class 10 or better |
| Power Supply | $8 | Official recommended |
| Optional: USB Speaker | $15-30 | Better audio than robot |
| **Total** | **$268-353** | One-time investment |

### 12.2 API Costs (Monthly)

**Deepgram** (Primary Voice Provider):
- **STT (Nova-2)**: $0.0043/minute
- **TTS (Aura)**: $0.015/1000 characters

**Anthropic Claude**:
- **Sonnet 4.5**: $3/million input tokens, $15/million output tokens

**Estimated Usage** (Moderate use: 5 interactions/day):
- **Voice interactions**: 150/month
- **Average interaction**: 10s command + 50-char response
- **STT cost**: 150 × 10s × $0.0043/60s = **$0.11/month**
- **TTS cost**: 150 × 50 chars × $0.015/1000 = **$0.11/month**
- **Claude cost**:
  - Input: ~2000 tokens/interaction × 150 = 300K tokens = **$0.90/month**
  - Output: ~500 tokens/interaction × 150 = 75K tokens = **$1.13/month**

**Total Monthly Cost**: ~**$2.25/month** (moderate use)

**Heavy Use** (20 interactions/day):
- **Total**: ~**$9/month**

### 12.3 Cost Comparison vs. Old Architecture

| Component | Old (Whisper + ElevenLabs) | New (Deepgram) | Savings |
|-----------|----------------------------|----------------|---------|
| STT | $0.006/min (Whisper API) | $0.0043/min | 28% |
| TTS | $0.30/1000 chars (ElevenLabs) | $0.015/1000 chars | 95% |
| **Monthly (moderate)** | **~$4.50** | **~$2.25** | **50%** |

**Key Advantages**:
1. **Deepgram is cheaper**: Especially TTS (20× cheaper than ElevenLabs)
2. **Better latency**: Deepgram optimized for real-time
3. **Simpler stack**: One provider for both STT and TTS
4. **Streaming support**: Better user experience

### 12.4 Cost Optimization Tips

1. **Wake word is crucial**: Prevents unnecessary API calls
2. **Cache common responses**: Weather, time, etc.
3. **Use Claude efficiently**: Provide clear context to minimize tokens
4. **Batch tool calls**: Combine multiple API calls where possible
5. **Monitor usage**: Set up alerts for unusual API usage
6. **Local fallbacks**: Use pre-recorded audio for very common responses

---

## 13. Future Enhancements

### 13.1 Advanced Autonomous Behaviors

- **Reinforcement Learning**: Train custom behaviors from demonstrations
- **Multi-Step Planning**: Claude plans complex multi-step tasks
- **Goal-Oriented Autonomy**: Give robot high-level goals ("clean up the room")
- **Learning from Experience**: Improve behaviors over time
- **Collaborative Multi-Robot**: Coordinate multiple Dash robots

### 13.2 Smart Home Integration

- **Home Assistant**: Control smart home devices
- **Scene Automation**: "Goodnight Dash" turns off lights, locks doors
- **Security Monitoring**: Patrol and report suspicious activity
- **Sensor Network**: Act as mobile sensor (temperature, air quality, etc.)
- **Voice Hub**: Central voice assistant for entire home

### 13.3 Computer Vision

- **Camera Mount**: Add Raspberry Pi Camera Module
- **Object Recognition**: Identify and locate objects
- **Face Recognition**: Recognize family members
- **Visual Navigation**: Navigate using visual landmarks
- **Gesture Control**: Respond to hand gestures

### 13.4 Advanced Communication

- **Multi-Language**: Support multiple languages dynamically
- **Emotion Detection**: Recognize user emotions from voice
- **Personality Modes**: Switch personalities (teacher, friend, assistant)
- **Storytelling Mode**: Interactive story generation with acting
- **Educational Content**: Tutor mode for kids

### 13.5 Extended Hardware Support

- **Cue Robot**: Support Cue-specific features (programmability, chat)
- **Custom Accessories**: Sketch kit, launcher, xylophone integration
- **Third-Party Sensors**: LIDAR, cameras, ultrasonic arrays
- **Custom Robots**: Adapt to other robot platforms (not just Wonder)

### 13.6 Cloud & Social Features

- **Cloud Sync**: Sync conversation history and learnings across devices
- **Skill Marketplace**: Download community-created skills
- **Behavior Sharing**: Share and download robot behaviors
- **Leaderboards**: Challenges and competitions
- **Remote Operation**: Securely control robot from anywhere

### 13.7 Performance & Reliability

- **On-Device LLM**: Run smaller LLM locally for offline mode
- **Hybrid Processing**: Local for simple tasks, cloud for complex
- **Battery Optimization**: Longer operation time
- **Faster Wake Word**: Custom wake word model for lower latency
- **Edge TPU**: Hardware acceleration for vision/ML tasks

---

## Conclusion

This roadmap transforms the WonderWorkshop Dash robot from a remote-controlled toy into an **autonomous AI agent** powered by Claude. The paradigm shift from web-controlled to robot-centric AI creates a fundamentally different—and more engaging—interaction model.

**Key Innovations**:
1. **Robot thinks for itself**: Claude agent runs on-robot, enabling true autonomy
2. **Voice-first interaction**: Natural conversation, not buttons and screens
3. **Cost-effective**: Deepgram provides high-quality voice at fraction of cost
4. **Extensible**: Skill and tool systems enable unlimited capabilities
5. **Safe by design**: Claude's reasoning validates all actions
6. **Production-ready**: Complete architecture from agent to monitoring

**Estimated Timeline**: 16 weeks (4 months) for full implementation

**Next Steps**:
1. Set up Raspberry Pi with initial environment
2. Get basic Claude agent running with text input
3. Add robot control via WonderPy
4. Implement voice pipeline with Deepgram
5. Build skill system and example skills
6. Add monitoring UI for oversight
7. Test, document, and deploy

**Success Metrics**:
- Robot responds to "Hey Dash" with >95% accuracy
- End-to-end voice interaction <2 seconds
- Successfully executes complex multi-step behaviors
- Safe autonomous operation (zero collisions in testing)
- Cost <$3/month for typical usage
- User satisfaction: "It feels like talking to a friend"

This is more than a robotics project—it's bringing AI agents into the physical world, making them accessible, safe, and genuinely useful. The future of robotics is conversational, autonomous, and intelligent. Let's build it.

---

**Document Version**: 2.0 (Major Paradigm Shift)
**Last Updated**: 2025-11-08
**Maintained By**: WonderPy AI-Autonomous Robot Development Team
