# Gary-Zero Agent Framework - Cline Project Rules

You are an AI coding assistant for the Gary-Zero autonomous agent framework. Follow these rules strictly to maintain consistency with the project's architecture and standards.

## Project Overview

Gary-Zero is a Railway.com-deployed autonomous AI agent framework with:

- **Cloud-Native**: Railway.com managed containerization (not Docker-first)
- **Multi-Agent**: Hierarchical agent cooperation and task delegation
- **Transparent**: Full visibility into agent reasoning and decision-making
- **Extensible**: Plugin architecture with MCP integration
- **Connected Services**: Kali Linux, E2B, Computer Use API, Morphism browser

## Core Development Rules

### AI Model Enforcement
CRITICAL: Only use approved models from `docs/ai-models.md`:
- **Anthropic**: Claude-4-Opus, Claude-4-Sonnet, Claude-Code, Claude-3.7-Sonnet
- **Google**: gemini-2.5-pro-preview-06-05, gemini-2.0-flash
- **OpenAI**: chatgpt-4.1, o1, o1-mini, o3-mini-2025-01-31, gpt-4.1-mini
- **Meta**: llama-3.3-70b-versatile
- **xAI**: grok-3, grok-3-mini

### Architecture Standards
- **Railway-First**: Use Railway managed containers, not Docker commands
- **Python 3.13+**: Modern Python with async/await patterns
- **FastAPI**: Web framework for API development
- **Agent OS Integration**: Follow .agent-os/ directory structure
- **MCP Protocol**: Both server and client capabilities

### Code Quality
- **TypeScript**: Strict typing, <200 lines per file
- **React**: Functional components with hooks
- **Testing**: Vitest (not Jest)
- **Package Manager**: yarn 4.9.1 (preferred), pnpm (secondary)
- **Ports**: Frontend 5675-5699, Backend 8765-8799

### Security & Performance
- Never commit secrets or hardcode credentials
- Use Railway environment variables with reference syntax
- Implement proper error handling and graceful degradation
- Follow async/await patterns for I/O operations

### Development Philosophy
1. **Build First**: Complete features rather than removing unused code
2. **Railway Native**: Design for Railway's managed infrastructure
3. **Agent Transparency**: All decisions must be visible and auditable
4. **Service Integration**: Leverage connected cloud services

### Connected Services
- **Kali Linux**: Security testing via Railway private network
- **E2B**: Code execution in sandboxed environment
- **Computer Use**: Desktop automation through Anthropic API
- **Morphism**: Browser automation service

## File Structure Awareness

```
Gary-Zero/
├── .agent-os/          # Agent OS coordination layer
│   ├── product/        # Product documentation
│   ├── instructions/   # Agent task guidance
│   └── specs/          # Agent specifications
├── docs/               # Technical documentation
├── framework/          # Core framework code
└── railway.toml        # Railway deployment config
```

## Key Commands
- Start development: Check existing package.json scripts
- Railway deployment: Use Railway CLI, not Docker
- Testing: Use Vitest test runner
- Linting: Follow .clinerules standards

## Agent Coordination
- Follow Agent OS patterns from .agent-os/instructions/
- Use MCP protocol for agent communication
- Implement hierarchical task delegation
- Maintain persistent memory across sessions

## Cline-Specific Notes
- Use existing .clinerules file for detailed coding standards
- Reference Agent OS instructions in .agent-os/instructions/
- Follow Railway-first deployment patterns
- Integrate with MCP task management system

Remember: Gary-Zero is the project name. Agent OS is the coordination framework from buildermethods.com that keeps us on track.
