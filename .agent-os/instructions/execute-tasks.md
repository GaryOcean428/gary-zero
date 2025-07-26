# Execute Tasks - Gary-Zero Agent Framework

## Context

This instruction guides the implementation of Gary-Zero features, ensuring adherence to Railway cloud architecture, agent framework principles, and development best practices.

## Implementation Guidelines

### 1. Railway Cloud Environment

- **Containerization**: Railway manages containers via Nixpacks/Railpack
- **Environment Variables**: Use Railway reference variables for service communication
- **Storage**: Implement with Railway volumes and cloud databases
- **Networking**: Leverage Railway's private network for service communication
- **Scaling**: Design for Railway's managed horizontal scaling

### 2. Agent Framework Requirements

- **Multi-Agent Support**: Hierarchical agent structure with task delegation
- **MCP Integration**: Both server and client capabilities
- **Real-time Communication**: WebSocket for agent coordination
- **Transparency**: All agent decisions must be visible and auditable
- **Extensibility**: Plugin architecture for community contributions

### 3. Connected Services Integration

- **Kali Linux Service**: Security testing via Railway private network
- **E2B Sandboxing**: Secure code execution in cloud environment
- **Anthropic Computer Use**: Desktop automation and visual interaction
- **Morphism Browser**: Web automation through Railway service

### 4. Development Standards

- **Python 3.13+**: Modern Python features and performance
- **FastAPI**: Async web framework with automatic documentation
- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust error recovery and user feedback
- **Security**: Input validation, authentication, and access controls

## Implementation Process

### Step 1: Environment Setup

- Verify Railway environment compatibility
- Configure environment variables and service references
- Set up local development with Railway CLI integration
- Ensure all connected services are accessible

### Step 2: Code Development

- Follow Gary-Zero code conventions from `.clinerules`
- Implement with Railway cloud constraints in mind
- Use async/await patterns for performance
- Include comprehensive error handling
- Add logging for debugging and monitoring

### Step 3: Service Integration

- Implement MCP protocol for agent communication
- Connect to Railway services using private network
- Handle service unavailability gracefully
- Include health checks and monitoring

### Step 4: Testing

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service-to-service communication
- **E2E Tests**: Complete user workflow testing
- **Railway Tests**: Cloud environment specific testing
- **Security Tests**: Vulnerability and penetration testing

### Step 5: Documentation

- Update technical documentation
- Add user guides and examples
- Document API endpoints and MCP interfaces
- Include troubleshooting guides

## Code Quality Requirements

### Architecture Alignment

- Cloud-native design patterns
- Agent-centric architecture
- Service-oriented communication
- Plugin-based extensibility

### Performance Standards

- Async/await for I/O operations
- Efficient resource utilization
- Railway scaling compatibility
- Response time optimization

### Security Implementation

- Railway managed isolation
- E2B sandboxing for code execution
- Input validation and sanitization
- Authentication and authorization
- Secure service communication

### Error Handling

- Graceful degradation when services unavailable
- User-friendly error messages
- Comprehensive logging and monitoring
- Recovery mechanisms for transient failures

## Railway Deployment Considerations

### Build Process

- Compatible with Nixpacks/Railpack builders
- Efficient dependency management
- Minimal container image size
- Fast build and deployment times

### Runtime Configuration

- Environment-based configuration
- Railway reference variables for service URLs
- Health check endpoints
- Proper port binding and networking

### Monitoring Integration

- Railway metrics and logging
- Custom application metrics
- Performance monitoring
- Error tracking and alerting

## Quality Gates

### Pre-Deployment Checklist

- [ ] Railway environment compatibility verified
- [ ] All tests passing (unit, integration, E2E)
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] MCP protocol compliance verified
- [ ] Connected services integration tested

### Post-Deployment Validation

- [ ] Health checks passing
- [ ] Service communication working
- [ ] User workflows functional
- [ ] Performance metrics acceptable
- [ ] Error rates within limits
- [ ] Agent coordination functioning

## Next Steps

After implementation:
- Deploy to Railway staging environment
- Conduct user acceptance testing
- Monitor performance and errors
- Gather feedback and iterate
- Update product documentation
- Plan next roadmap features

This instruction ensures all implementation work aligns with Gary-Zero's cloud-native, agent-focused architecture while maintaining high quality and user experience standards.
