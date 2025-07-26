# Technology Stack - Gary-Zero

## Core Architecture

### Runtime Environment

- **Language**: Python 3.13+ (primary), JavaScript/TypeScript (UI)
- **Framework**: FastAPI for async API, Flask for legacy support
- **Cloud Platform**: Railway.com managed containerization with Nixpacks/Railpack
- **Process Management**: Uvicorn ASGI server with Railway's managed scaling

### Backend Technologies

#### Web Framework & API

- **FastAPI 0.115.0+**: Modern async web framework
- **Uvicorn 0.32.0+**: ASGI server with standard features
- **Pydantic 2.8.0+**: Data validation and settings management
- **WebSockets 12.0+**: Real-time bidirectional communication

#### AI & Language Models

- **LangChain Core 0.3.0+**: LLM abstraction and orchestration
- **LangChain Anthropic 0.3.3+**: Claude integration
- **LangChain OpenAI 0.3.11+**: GPT integration
- **Custom Model Registry**: Support for multiple AI providers

#### Agent Communication & Protocols

- **MCP (Model Context Protocol) 1.12.0+**: Agent interoperability
- **FastMCP 2.3.0+**: High-performance MCP implementation
- **Shared-MCP**: Custom MCP extensions for multi-agent systems
- **WebSocket**: Real-time agent communication

#### Task Orchestration & Execution

- **Railway Services**: Managed container orchestration and service communication
- **Playwright 1.45.0+**: Web automation and browser control
- **Anthropic Computer Use**: Desktop automation and visual interaction
- **E2B SDK**: Cloud code execution and sandboxing
- **PSUtil 7.0.0+**: System monitoring and resource management
- **AsyncIO-MQTT 0.16.0+**: Asynchronous message queuing

### Frontend Technologies

#### Web Interface

- **Vanilla JavaScript/TypeScript**: Lightweight, dependency-free UI
- **CSS3**: Modern styling with CSS Grid and Flexbox
- **WebSocket API**: Real-time UI updates
- **Progressive Web App**: Installable web application

#### Static Assets Management

- **FastAPI StaticFiles**: Efficient static file serving
- **Responsive Design**: Mobile-first approach
- **Component Architecture**: Modular UI components

### Database & Storage

#### Memory & Knowledge Management

- **Vector Database**: Cloud-hosted vector storage for memory
- **Railway Volumes**: Persistent storage for critical data
- **External Services**: PostgreSQL, Redis for scalable storage
- **JSON Configuration**: Environment-based settings management

#### Session Management

- **In-Memory Sessions**: Fast session state management
- **Cloud Memory**: Distributed long-term agent memory storage
- **Database Storage**: Configuration and user data in managed databases

### Security & Authentication

#### Security Framework

- **HTTPBearer**: Token-based authentication
- **CORS Middleware**: Cross-origin request handling
- **GZip Middleware**: Response compression
- **Input Validation**: Pydantic-based request validation

#### Secure Execution

- **Railway Isolation**: Managed container security and isolation
- **Secret Management**: Environment-based secret handling
- **Permission Controls**: Fine-grained access controls
- **Security Scanning**: Automated vulnerability detection

### Development & Deployment

#### Code Quality & Testing

- **Pytest 8.2.0+**: Comprehensive testing framework
- **Pytest-AsyncIO**: Async testing support
- **Black 24.4.0+**: Code formatting
- **Ruff 0.11.13+**: Fast Python linter
- **MyPy 1.10.0+**: Static type checking

#### CI/CD Pipeline

- **GitHub Actions**: Automated testing and deployment
- **Docker Hub**: Container registry
- **Railway**: Cloud deployment platform
- **Quality Gates**: Multi-stage validation pipeline

#### Development Tools

- **Pre-commit**: Git hooks for code quality
- **Poetry/Pip**: Dependency management
- **Railway CLI**: Cloud-native development workflow
- **Hot Reload**: Railway's development server with auto-restart

### Infrastructure & Deployment

#### Cloud Deployment

- **Railway**: Primary cloud platform with inter-service communication
- **Managed Containers**: Railway's automated containerization with Nixpacks/Railpack
- **Environment Variables**: Configuration management with Railway reference variables
- **Health Checks**: Application monitoring and service discovery
- **Private Networking**: Railway's internal service communication

#### Networking & Communication

- **HTTP/HTTPS**: Web protocol support
- **WebSocket**: Real-time communication
- **TCP/UDP**: Network protocol support
- **Reverse Proxy**: Production-ready routing

### Application Framework

#### Agent OS Workflow Engine

- **Multi-Agent Orchestration**: Hierarchical agent coordination system
- **Task Delegation**: Automatic subtask distribution across agent personas
- **Workflow State Management**: Persistent workflow execution state
- **Agent Role Mapping**: Dynamic role assignment based on task requirements
- **Decision Coordination**: Integrated decision-making with authoritative persona rules

#### Vector Memory System

- **Persistent Agent Memory**: Long-term context retention across sessions
- **Vector Storage**: Embedded vector database for semantic memory search
- **Memory Consolidation**: Automatic memory summarization and optimization
- **Cross-Agent Memory Sharing**: Shared knowledge base across agent instances
- **Memory Analytics**: Usage patterns and memory effectiveness tracking

#### Agent Registry

- **Dynamic Agent Discovery**: Runtime agent capability registration
- **Persona Mapping**: Gary8D agent persona to Agent OS role mapping
- **Capability Matching**: Automatic agent selection based on task requirements
- **Load Balancing**: Intelligent agent workload distribution
- **Health Monitoring**: Agent availability and performance tracking

### Integration & Extensibility

#### Plugin System

- **Dynamic Loading**: Runtime plugin discovery
- **Python Modules**: Native Python plugin architecture
- **Configuration Driven**: YAML/JSON plugin configuration
- **Event System**: Plugin communication framework

#### External Dependencies & Cloud Services

- **Agent OS Coordination Layer**: Primary orchestration system for multi-agent workflows
- **Gary8D Agent Personas**: Specialized expert agents for domain-specific tasks
- **MCP Protocol Stack**: Model Context Protocol for agent interoperability
- **Vector Database Services**: External vector storage for scalable memory systems
- **Task Queue Systems**: Redis, RabbitMQ for distributed task processing
- **Kali Linux Service**: Railway-hosted penetration testing environment
- **E2B Code Execution**: Secure cloud code execution sandbox
- **Morphism Browser**: Railway-deployed browser automation service

#### External Integrations

- **Search Engines**: SearXNG, DuckDuckGo, Perplexity
- **AI Providers**: OpenAI, Anthropic, Google, local models
- **Development Tools**: VSCode, Git, GitHub
- **Cloud Services**: Railway, Docker Hub, various APIs

## Performance & Scalability

### Optimization Features

- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Efficient resource management
- **Caching**: Memory and disk-based caching
- **Compression**: GZip response compression

### Monitoring & Observability

- **Performance Metrics**: Built-in performance monitoring
- **Logging System**: Structured logging with multiple levels
- **Health Endpoints**: Application health monitoring
- **Resource Tracking**: Memory and CPU usage monitoring

## Architecture Principles

### Design Patterns

- **Microservices**: Modular service architecture
- **Event-Driven**: Asynchronous event processing
- **Plugin Architecture**: Extensible component system
- **Configuration as Code**: Infrastructure and settings management

### Quality Attributes

- **Scalability**: Horizontal and vertical scaling support
- **Reliability**: Fault tolerance and error recovery
- **Maintainability**: Clean, documented, and testable code
- **Security**: Defense in depth with multiple security layers
- **Performance**: Optimized for speed and resource efficiency
