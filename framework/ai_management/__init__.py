"""
AI Management Module for Gary-Zero Agent Framework

This module provides comprehensive AI model management, routing, caching,
and optimization capabilities for the Gary-Zero agent framework.

Key Features:
- Multi-provider model management (OpenAI, Anthropic, Google, Groq, etc.)
- Intelligent model routing and load balancing
- Response caching and cost optimization
- A/B testing for model performance (optional)
- Version management and rollback capabilities
- Prompt template management and optimization
- AI-Manus integration for enhanced capabilities

Components:
- CacheManager: Response caching and optimization
- CostOptimizer: Cost tracking and optimization
- ModelRouter: Model routing and load balancing
- PromptManager: Prompt template management
- VersionManager: Model version control
- MCPIntegrationManager: Model Context Protocol integration
- AiManusIntegrationManager: AI-Manus feature integration
"""

# Core imports that should always work
from .caching import ModelCacheManager as CacheManager
from .cost_optimizer import CostOptimizer
from .routing import ModelRouter
from .prompt_manager import PromptManager
from .version_manager import ModelVersionManager as VersionManager

# AI-Manus integration
from .mcp_integration import MCPIntegrationManager, initialize_mcp_integration
from .ai_manus_integration import (
    AiManusIntegrationManager, 
    AiManusFeatures,
    initialize_ai_manus_integration,
    create_development_config,
    create_production_config,
    create_minimal_config
)

# Conditional imports for optional features
try:
    from .model_manager import ModelManager
    MODEL_MANAGER_AVAILABLE = True
except ImportError:
    MODEL_MANAGER_AVAILABLE = False
    ModelManager = None

try:
    from .ab_testing import ABTestManager
    AB_TESTING_AVAILABLE = True
except ImportError:
    AB_TESTING_AVAILABLE = False
    ABTestManager = None

__all__ = [
    'CacheManager', 
    'CostOptimizer',
    'ModelRouter',
    'PromptManager',
    'VersionManager',
    'MCPIntegrationManager',
    'initialize_mcp_integration',
    'AiManusIntegrationManager',
    'AiManusFeatures',
    'initialize_ai_manus_integration',
    'create_development_config',
    'create_production_config',
    'create_minimal_config',
    'MODEL_MANAGER_AVAILABLE',
    'AB_TESTING_AVAILABLE'
]

if MODEL_MANAGER_AVAILABLE:
    __all__.append('ModelManager')

if AB_TESTING_AVAILABLE:
    __all__.append('ABTestManager')

__version__ = "1.1.0"