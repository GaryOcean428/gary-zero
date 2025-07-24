# Multi-Agent Workflow Patterns

This document describes workflow patterns for coordinating multiple AI coding assistants in the Gary-Zero development environment.

## Overview

Gary-Zero supports a multi-agent development approach where different AI assistants can work together on the same codebase while maintaining consistency through shared configuration and standards.

## Supported AI Assistants

### Primary Agents
- **Claude Code**: Main development assistant with full MCP integration
- **Cline**: VSCode extension for file operations and code generation
- **Windsurf**: Advanced code understanding and refactoring
- **Warp AI**: Terminal-focused command assistance
- **GitHub Copilot**: Real-time code suggestions and completions

### Configuration Files
- **Claude Code**: `CLAUDE.md` (this file)
- **Cline**: `cline_docs/projectRules.md`
- **Windsurf**: `.windsurfrules`
- **Warp AI**: `.warp/ai_rules.md`
- **GitHub Copilot**: `.github/copilot-rules.md`

## Workflow Patterns

### 1. Sequential Development Pattern

**Use Case**: Complex feature development requiring multiple phases

**Process**:
1. **Planning Phase** (Claude Code): Use Agent OS planning instructions
2. **Implementation Phase** (Cline): File creation and core logic
3. **Refinement Phase** (Windsurf): Code optimization and refactoring
4. **Testing Phase** (Claude Code): Vitest test creation and execution
5. **Deployment Phase** (Warp AI): Railway CLI deployment commands

**Benefits**:
- Clear separation of concerns
- Specialized AI for each development phase
- Consistent handoff between agents

### 2. Parallel Development Pattern

**Use Case**: Multiple developers working on different features simultaneously

**Process**:
1. Each developer uses their preferred AI assistant
2. All assistants follow the same `.clinerules` standards
3. Railway environment ensures consistent deployment
4. MCP protocol enables agent communication

**Benefits**:
- Team flexibility in AI tool choice
- Consistent code quality across assistants
- No merge conflicts from different AI patterns

### 3. Collaborative Review Pattern

**Use Case**: Code review and quality assurance

**Process**:
1. **Initial Development** (Any AI assistant)
2. **Security Review** (Claude Code with security focus)
3. **Performance Review** (Windsurf optimization)
4. **Documentation** (GitHub Copilot suggestions)
5. **Final Testing** (Cline with Vitest)

**Benefits**:
- Multiple AI perspectives on code quality
- Comprehensive review coverage
- Specialized expertise for each review aspect

### 4. Command Chain Pattern

**Use Case**: Complex operations requiring multiple tools

**Process**:
1. **Warp AI**: Generate Railway CLI commands
2. **Claude Code**: Execute commands with error handling
3. **Cline**: File modifications based on deployment results
4. **GitHub Copilot**: Code suggestions for fixes

**Benefits**:
- Specialized AI for each operation type
- Error handling at each step
- Seamless tool integration

## Coordination Mechanisms

### Shared Configuration

All AI assistants reference the same core standards:

```text
Primary Source: .clinerules
├── AI Model Enforcement (docs/ai-models.md)
├── Railway Architecture Patterns
├── Code Quality Standards
├── Security Requirements
└── Testing Guidelines
```

### Agent OS Integration

The `.agent-os/` directory provides coordination:

- **Instructions**: Task execution guidance for all agents
- **Product**: Shared product documentation
- **Specs**: Agent specification templates

### Environment Consistency

Railway.com deployment ensures:
- Consistent environment variables across all agents
- Managed containerization (no Docker conflicts)
- Shared service access (Kali, E2B, Computer Use, Morphism)

## Best Practices

### 1. Agent Selection

Choose the right AI assistant for the task:

- **Complex Planning**: Claude Code (MCP + Agent OS)
- **File Operations**: Cline (VSCode integration)
- **Code Analysis**: Windsurf (deep understanding)
- **Terminal Work**: Warp AI (command expertise)
- **Real-time Suggestions**: GitHub Copilot (IDE integration)

### 2. Handoff Protocols

When switching between agents:

1. **Document Current State**: Update relevant files
2. **Check Standards Compliance**: Verify .clinerules adherence
3. **Update Agent OS**: Record progress in .agent-os/specs/
4. **Test Functionality**: Ensure working state before handoff

### 3. Conflict Resolution

When agents produce conflicting approaches:

1. **Reference .clinerules**: Primary source of truth
2. **Check Agent OS Product Docs**: Mission alignment
3. **Railway Compatibility**: Cloud-native requirements
4. **Security First**: Follow security specialist guidance

### 4. Quality Gates

Before completing multi-agent workflows:

- [ ] All agents followed .clinerules standards
- [ ] Code passes Vitest test suite
- [ ] Railway deployment successful
- [ ] Security review completed
- [ ] Documentation updated

## Integration Examples

### Example 1: Feature Development

```bash
# Warp AI: Start development server
railway run yarn dev

# Claude Code: Plan feature in Agent OS
# (Uses .agent-os/instructions/plan-product.md)

# Cline: Implement core functionality
# (References cline_docs/projectRules.md)

# Windsurf: Optimize and refactor
# (Follows .windsurfrules standards)

# GitHub Copilot: Add inline documentation
# (Uses .github/copilot-rules.md patterns)

# Claude Code: Run tests and deploy
railway run yarn test
railway up
```

### Example 2: Bug Investigation

```bash
# Warp AI: Check Railway logs
railway logs

# Claude Code: Analyze error patterns
# (Uses diagnostic specialists from .clinerules)

# Cline: Fix identified issues
# (Implements according to cline_docs/projectRules.md)

# Windsurf: Verify fix quality
# (Applies .windsurfrules optimization)

# Claude Code: Test and validate
railway run yarn test
```

## Monitoring and Metrics

### Agent Performance Tracking

Monitor multi-agent effectiveness:

- **Code Quality**: Consistent across all agents
- **Deployment Success**: Railway compatibility
- **Test Coverage**: Vitest results
- **Security Compliance**: No hardcoded secrets
- **Documentation**: Up-to-date specifications

### Configuration Drift Detection

Prevent inconsistencies:

- Regular comparison of agent configuration files
- Automated checks for .clinerules compliance
- Railway environment variable validation
- MCP protocol compatibility testing

## Future Enhancements

### Planned Improvements

1. **Agent Orchestration**: Automated agent selection and handoff
2. **Real-time Coordination**: WebSocket communication between agents
3. **Shared Memory**: Vector database for cross-agent knowledge
4. **Workflow Templates**: Pre-defined multi-agent patterns
5. **Performance Analytics**: Agent effectiveness metrics

### Integration Roadmap

- **Phase 1**: Configuration standardization (Current)
- **Phase 2**: Agent communication protocols
- **Phase 3**: Automated workflow orchestration
- **Phase 4**: AI-driven agent selection and coordination

This multi-agent approach ensures Gary-Zero development maintains high quality and consistency regardless of which AI assistants team members prefer to use.
