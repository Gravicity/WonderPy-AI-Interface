# WonderPy AI-Enhanced Full-Stack Control System 🤖

![WonderWorkshop Dash Robot](https://via.placeholder.com/800x200/0066cc/ffffff?text=WonderPy+AI-Interface)

A comprehensive, AI-enhanced, full-stack control system for WonderWorkshop robots (Dash, Dot, and Cue). This project transforms the original WonderPy library into a modern, production-ready platform featuring:

- 🎮 **REST + WebSocket API** for real-time robot control
- 🌐 **Responsive Web UI** with live sensor visualization
- 🤖 **AI Agent Integration** (Claude API) for natural language control
- 🎤 **Voice Interface** with Whisper STT and ElevenLabs TTS
- 🔌 **Plugin System** for extensible robot behaviors
- 🐳 **Docker Deployment** for portable infrastructure
- 🔄 **CI/CD Pipeline** with GitHub Actions

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Plugin Development](#plugin-development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## ✨ Features

### Backend (FastAPI)
- ⚡ High-performance async API with WebSocket support
- 🔐 JWT authentication and authorization
- 🛡️ Multi-tier safety validation for robot commands
- 📊 Real-time sensor streaming at ~30 Hz
- 🧠 LangChain-powered AI agent orchestration
- 🎵 Audio processing pipeline (STT/TTS)
- 🔌 Extensible plugin architecture

### Frontend (React + TypeScript)
- 📱 Responsive, mobile-friendly interface
- 📈 Real-time sensor charts and visualizations
- 🎨 Beautiful UI components (shadcn/ui + Tailwind)
- 🎙️ Voice interface with wake word detection
- 💬 AI chat console with streaming responses
- 🎮 Intuitive robot control panel
- 📊 3D robot visualization (Three.js)

### AI & Voice
- 🧠 **Claude Sonnet 4.5** for natural language understanding
- 🗣️ **Whisper** for accurate speech-to-text
- 🔊 **ElevenLabs** for high-quality text-to-speech
- 👂 **Silero VAD** for voice activity detection
- 🎯 **Picovoice Porcupine** for wake word detection
- 🧬 **ChromaDB** RAG for robot memory

### DevOps
- 🐳 Full Docker Compose stack
- 📊 Prometheus + Grafana monitoring
- 📝 ELK stack for centralized logging
- 🔄 Automated CI/CD with GitHub Actions
- ✅ Comprehensive test coverage

---

## 🏗️ Architecture

```
┌─────────────┐      HTTP/WSS      ┌──────────────┐      Bluetooth     ┌─────────────┐
│   Browser   │ ◄────────────────► │   FastAPI    │ ◄───────────────► │ Dash Robot  │
│   (React)   │                    │   Backend    │                    │ (WonderPy)  │
└─────────────┘                    └──────────────┘                    └─────────────┘
     │  │  │                            │    │    │
     │  │  └──── WebSocket ─────────────┤    │    │
     │  └─────── REST API ──────────────┘    │    │
     └──────── Voice Stream ─────────────────┘    │
                                                   │
                           ┌───────────────────────┴──────────────┐
                           │                                       │
                    ┌──────▼──────┐                       ┌───────▼────────┐
                    │  PostgreSQL │                       │  Claude API    │
                    │   + Redis   │                       │ ElevenLabs API │
                    └─────────────┘                       └────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE_ROADMAP.md](ARCHITECTURE_ROADMAP.md).

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 20+**
- **Docker & Docker Compose** (for containerized deployment)
- **Bluetooth** support (for robot connection)
- **API Keys**:
  - Anthropic Claude API key
  - ElevenLabs API key (optional, for TTS)
  - OpenAI API key (optional, for Whisper cloud)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/WonderPy-AI-Interface.git
cd WonderPy-AI-Interface

# Copy environment file and configure
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Start the backend
uvicorn api.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

---

## 🛠️ Development

### Project Structure

```
WonderPy-AI-Interface/
├── backend/              # Python FastAPI backend
│   ├── api/             # API routes and schemas
│   ├── services/        # Business logic services
│   ├── core/            # Core functionality (WonderPy adapter)
│   ├── models/          # Database models
│   ├── plugins/         # Plugin system
│   └── tests/           # Test suite
├── frontend/            # React TypeScript frontend
│   └── src/
│       ├── components/  # React components
│       ├── hooks/       # Custom React hooks
│       ├── services/    # API clients
│       └── store/       # State management
├── docker/              # Docker configuration
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov

# Frontend tests
cd frontend
npm run test
```

### Code Quality

```bash
# Backend linting
black backend/
isort backend/
mypy backend/

# Frontend linting
cd frontend
npm run lint
```

---

## 📚 API Documentation

Once the backend is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Example API Calls

#### Connect to Robot

```bash
curl -X POST http://localhost:8000/api/v1/robots/connect \
  -H "Content-Type: application/json" \
  -d '{"robot_name": "Dash", "timeout": 30}'
```

#### Move Robot Forward

```bash
curl -X POST http://localhost:8000/api/v1/robots/robot-001/commands/move \
  -H "Content-Type: application/json" \
  -d '{
    "action": "forward",
    "distance_cm": 50,
    "speed_cm_s": 20
  }'
```

#### Get Sensor Data

```bash
curl http://localhost:8000/api/v1/robots/robot-001/sensors/all
```

---

## 🔌 Plugin Development

Create custom robot behaviors using the plugin system. See [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md) for details.

### Example Plugin

```python
from plugins.base import RobotBehavior

class PatrolBehavior(RobotBehavior):
    """Simple patrol behavior"""

    def on_configure(self, robot, config):
        self.robot = robot
        self.waypoints = config.get('waypoints', [(0, 0), (1, 1)])
        return True

    def execute(self):
        for waypoint in self.waypoints:
            self.robot.body.do_pose(waypoint[0], waypoint[1], 0)
        return True

# Register in pyproject.toml
[project.entry-points."wonderpy.behaviors"]
patrol = "my_plugin:PatrolBehavior"
```

---

## 🚢 Deployment

### Production Deployment (Raspberry Pi)

```bash
# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp backend/.env.example backend/.env
nano backend/.env  # Add API keys

# Start with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Access at http://raspberrypi.local
```

### Cloud Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for AWS, GCP, and Azure deployment guides.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **WonderWorkshop** for creating amazing educational robots
- **playi** for the original [WonderPy](https://github.com/playi/WonderPy) library
- **Anthropic** for Claude AI
- **OpenAI** for Whisper
- **ElevenLabs** for high-quality TTS

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/WonderPy-AI-Interface/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/WonderPy-AI-Interface/discussions)

---

## 🗺️ Roadmap

- [x] Phase 1: Foundation (Backend + Basic Frontend)
- [x] Phase 2: AI Integration (Claude API + Chat UI)
- [ ] Phase 3: Voice Features (Whisper + ElevenLabs)
- [ ] Phase 4: Plugin System
- [ ] Phase 5: DevOps & Deployment
- [ ] Phase 6: Polish & Enhancement
- [ ] Multi-robot fleet management
- [ ] Computer vision integration
- [ ] Mobile app (React Native)

See [ARCHITECTURE_ROADMAP.md](ARCHITECTURE_ROADMAP.md) for detailed development timeline.

---

**Made with ❤️ by the WonderPy AI-Interface Team**
