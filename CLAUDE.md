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
- **Docker-First Architecture**: Consistent deployment across all environments
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
**Deployment**: Docker-first with Railway cloud integration  

For detailed technical information, architecture decisions, and development roadmap, refer to the product documentation in the `.agent-os/product/` directory.
