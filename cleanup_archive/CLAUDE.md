# CLAUDE.md


## Gary-Zero Agent OS Project Overview

Gary-Zero is an autonomous AI agent framework that enables users to build, deploy, and orchestrate intelligent agents for complex task automation. The project follows Agent OS principles with comprehensive product documentation.

### Product Documentation

The complete product specification is maintained in the `.agent-os/product/` directory:

- **[Mission Statement](.agent-os/product/mission.md)** - Core mission, vision, and value proposition
- **[Technology Stack](.agent-os/product/tech-stack.md)** - Complete technical architecture and dependencies
- **[Development Roadmap](.agent-os/product/roadmap.md)** - Product evolution phases and future plans
- **[Architecture Decisions](.agent-os/product/decisions.md)** - Key design decisions and rationale

### Development Guidelines

Development is guided by the rules specified in the `.clinerules` file, which enforces standards across TypeScript, React, and multi-agent systems. This ensures all development aligns with best practices.

Claude Rules are found in .clinerules file in the root directory of the repository.

### Key Features

- **Multi-Agent Cooperation**: Hierarchical agent structure for complex task delegation
- **Complete Transparency**: Full visibility into agent reasoning and decision-making
- **Railway-Managed Infrastructure**: Consistent cloud-native deployment with managed containerization
- **MCP Integration**: Both server and client capabilities for ecosystem interoperability
- **Extensible Plugin System**: Dynamic tool and functionality extension
- **Real-time Communication**: WebSocket-based bidirectional communication
- **Persistent Memory**: Learning and context retention across sessions

### Target Users

1. **Developers**: Rapid AI application prototyping with extensive customization
2. **Researchers**: Transparent framework for studying multi-agent interactions
3. **Business Users**: Automated workflows without requiring coding expertise
4. **Security Professionals**: Specialized cybersecurity and penetration testing tools

### Current Status

**Version**: 0.9.0 (Beta)
**License**: MIT
**Python**: 3.13+ required
**Deployment**: Railway.com cloud-native with managed containerization

For detailed technical information, architecture decisions, and development roadmap, refer to the product documentation in the `.agent-os/product/` directory.

### Cross-Agent AI Assistant Compatibility

Gary-Zero includes configuration files for multiple AI coding assistants to ensure consistent development standards across the team:

#### Supported AI Assistants

- **Claude Code**: Primary development assistant (this file)
- **Cline**: Project rules in `cline_docs/projectRules.md`
- **Windsurf**: Rules in `.windsurfrules`
- **Warp AI**: Terminal-focused rules in `.warp/ai_rules.md`
- **GitHub Copilot**: Code suggestions in `.github/copilot-rules.md`

#### Universal Development Standards

All AI assistants are configured to follow:

1. **Railway-First Architecture**: Cloud-native deployment patterns
2. **AI Model Enforcement**: Only approved models from `docs/ai-models.md`
3. **Agent OS Integration**: Follow `.agent-os/` directory structure
4. **Code Quality**: TypeScript strict typing, Vitest testing, sub-200 line files
5. **Security**: No hardcoded secrets, Railway environment variables
6. **MCP Protocol**: Multi-agent communication standards

#### Configuration Synchronization

The primary source of truth for development rules is the `.clinerules` file. All assistant-specific configuration files derive from and reference these core standards to maintain consistency across different AI tools and team members.
