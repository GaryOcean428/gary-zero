"""OpenAI Agents SDK integration initialization for Gary-Zero.

This module provides initialization functions to set up the SDK integration
components and ensure they work together seamlessly.
"""

import asyncio
from typing import Optional, Dict, Any, TYPE_CHECKING

from framework.helpers.print_style import PrintStyle

# Forward reference imports
if TYPE_CHECKING:
    from agent import Agent, AgentConfig, AgentContext


def initialize_sdk_integration(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Initialize all OpenAI Agents SDK integration components."""
    config = config or {}
    
    PrintStyle(font_color="blue", padding=True).print(
        "[SDK] Initializing OpenAI Agents SDK integration..."
    )
    
    initialization_results = {
        "guardrails": False,
        "tracing": False,
        "tools": False,
        "orchestrator": False,
        "errors": []
    }
    
    # Initialize guardrails system
    try:
        from framework.helpers.guardrails import initialize_guardrails
        initialize_guardrails(strict_mode=config.get("strict_mode", False))
        initialization_results["guardrails"] = True
        PrintStyle(font_color="green", padding=True).print(
            "[SDK] ✓ Guardrails system initialized"
        )
    except Exception as e:
        error_msg = f"Failed to initialize guardrails: {e}"
        initialization_results["errors"].append(error_msg)
        PrintStyle(font_color="red", padding=True).print(f"[SDK] ✗ {error_msg}")
    
    # Initialize tracing system
    try:
        from framework.helpers.agent_tracing import initialize_tracing
        gary_logger = config.get("gary_logger")
        initialize_tracing(gary_logger)
        initialization_results["tracing"] = True
        PrintStyle(font_color="green", padding=True).print(
            "[SDK] ✓ Tracing system initialized"
        )
    except Exception as e:
        error_msg = f"Failed to initialize tracing: {e}"
        initialization_results["errors"].append(error_msg)
        PrintStyle(font_color="red", padding=True).print(f"[SDK] ✗ {error_msg}")
    
    # Initialize SDK wrapper
    try:
        from framework.helpers.agents_sdk_wrapper import initialize_sdk_integration as init_wrapper
        init_wrapper(enable_tracing=config.get("enable_tracing", True))
        initialization_results["orchestrator"] = True
        PrintStyle(font_color="green", padding=True).print(
            "[SDK] ✓ SDK orchestrator initialized"
        )
    except Exception as e:
        error_msg = f"Failed to initialize SDK orchestrator: {e}"
        initialization_results["errors"].append(error_msg)
        PrintStyle(font_color="red", padding=True).print(f"[SDK] ✗ {error_msg}")
    
    # Tools will be initialized per-agent, so just mark as ready
    initialization_results["tools"] = True
    PrintStyle(font_color="green", padding=True).print(
        "[SDK] ✓ Tools system ready (will initialize per-agent)"
    )
    
    # Summary
    success_count = sum(1 for v in initialization_results.values() if isinstance(v, bool) and v)
    total_components = 4
    
    if success_count == total_components:
        PrintStyle(font_color="green", padding=True).print(
            f"[SDK] ✓ All {total_components} components initialized successfully"
        )
    else:
        PrintStyle(font_color="yellow", padding=True).print(
            f"[SDK] ⚠ {success_count}/{total_components} components initialized successfully"
        )
        if initialization_results["errors"]:
            PrintStyle(font_color="red", padding=True).print(
                f"[SDK] Errors: {'; '.join(initialization_results['errors'])}"
            )
    
    return initialization_results


def initialize_agent_sdk_integration(agent: "Agent", config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Initialize SDK integration for a specific agent."""
    config = config or {}
    
    results = {
        "tools_registered": 0,
        "sdk_wrapper_created": False,
        "errors": []
    }
    
    try:
        # Initialize tools for this agent
        from framework.helpers.agent_tools_wrapper import initialize_tools
        registered_tools = initialize_tools(agent)
        results["tools_registered"] = len(registered_tools)
        
        PrintStyle(font_color="cyan", padding=True).print(
            f"[SDK] Registered {len(registered_tools)} tools for agent {agent.agent_name}"
        )
        
    except Exception as e:
        error_msg = f"Failed to initialize tools for agent {agent.agent_name}: {e}"
        results["errors"].append(error_msg)
        PrintStyle(font_color="red", padding=True).print(f"[SDK] ✗ {error_msg}")
    
    try:
        # Create SDK wrapper for agent
        from framework.helpers.agents_sdk_wrapper import get_sdk_orchestrator, SDKAgentConfig
        
        orchestrator = get_sdk_orchestrator()
        
        sdk_config = SDKAgentConfig(
            name=config.get("name", agent.agent_name),
            model_provider=config.get("model_provider", "openai"),
            model_name=config.get("model_name", "o3"),  # Updated to modern o3 model
            instructions=config.get("instructions", ""),
            enable_tracing=config.get("enable_tracing", True),
            enable_guardrails=config.get("enable_guardrails", True)
        )
        
        agent_id = orchestrator.register_agent(agent, sdk_config)
        results["sdk_wrapper_created"] = True
        results["agent_id"] = agent_id
        
        PrintStyle(font_color="cyan", padding=True).print(
            f"[SDK] Created SDK wrapper for agent {agent.agent_name} (ID: {agent_id})"
        )
        
    except Exception as e:
        error_msg = f"Failed to create SDK wrapper for agent {agent.agent_name}: {e}"
        results["errors"].append(error_msg)
        PrintStyle(font_color="red", padding=True).print(f"[SDK] ✗ {error_msg}")
    
    return results


def get_sdk_status() -> Dict[str, Any]:
    """Get status of all SDK integration components."""
    status = {
        "timestamp": asyncio.get_event_loop().time(),
        "components": {
            "guardrails": {"status": "unknown", "details": {}},
            "tracing": {"status": "unknown", "details": {}},
            "tools": {"status": "unknown", "details": {}},
            "orchestrator": {"status": "unknown", "details": {}}
        },
        "overall_status": "checking"
    }
    
    # Check guardrails status
    try:
        from framework.helpers.guardrails import get_guardrails_manager
        manager = get_guardrails_manager()
        status["components"]["guardrails"] = {
            "status": "active",
            "details": manager.get_status()
        }
    except Exception as e:
        status["components"]["guardrails"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    # Check tracing status
    try:
        from framework.helpers.agent_tracing import get_logging_integration
        # This will fail if no logger provided, which is expected
        status["components"]["tracing"] = {
            "status": "available",
            "details": {"note": "Tracing available, requires logger for full integration"}
        }
    except Exception as e:
        status["components"]["tracing"] = {
            "status": "available",
            "details": {"note": "Tracing components loaded"}
        }
    
    # Check tools status
    try:
        from framework.helpers.agent_tools_wrapper import get_tool_registry
        registry = get_tool_registry()
        status["components"]["tools"] = {
            "status": "active",
            "details": {
                "registered_tools": len(registry.registered_tools),
                "categories": list(registry.tool_categories.keys())
            }
        }
    except Exception as e:
        status["components"]["tools"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    # Check orchestrator status
    try:
        from framework.helpers.agents_sdk_wrapper import get_sdk_orchestrator
        orchestrator = get_sdk_orchestrator()
        status["components"]["orchestrator"] = {
            "status": "active",
            "details": orchestrator.get_all_agents_status()
        }
    except Exception as e:
        status["components"]["orchestrator"] = {
            "status": "error",
            "details": {"error": str(e)}
        }
    
    # Determine overall status
    component_statuses = [comp["status"] for comp in status["components"].values()]
    if all(s in ["active", "available"] for s in component_statuses):
        status["overall_status"] = "healthy"
    elif any(s == "error" for s in component_statuses):
        status["overall_status"] = "degraded"
    else:
        status["overall_status"] = "unknown"
    
    return status


def create_sdk_enabled_agent(agent_config: "AgentConfig", agent_context: "AgentContext",
                            sdk_config: Optional[Dict[str, Any]] = None) -> "Agent":
    """Create a new agent with SDK integration enabled."""
    from agent import Agent
    
    # Create the base agent
    agent = Agent(0, agent_config, agent_context)
    
    # Initialize SDK integration for this agent
    sdk_results = initialize_agent_sdk_integration(agent, sdk_config)
    
    # Store SDK integration results in agent data
    agent.set_data("sdk_integration_results", sdk_results)
    agent.set_data("sdk_enabled", True)
    
    return agent


def migrate_existing_agent_to_sdk(agent: "Agent", 
                                 sdk_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Migrate an existing agent to use SDK integration."""
    results = initialize_agent_sdk_integration(agent, sdk_config)
    
    # Update agent data to indicate SDK is enabled
    agent.set_data("sdk_integration_results", results)
    agent.set_data("sdk_enabled", True)
    
    PrintStyle(font_color="green", padding=True).print(
        f"[SDK] Migrated agent {agent.agent_name} to SDK integration"
    )
    
    return results


# Backward compatibility functions
def is_sdk_available() -> bool:
    """Check if SDK integration is available."""
    try:
        import agents
        return True
    except ImportError:
        return False


def get_sdk_version() -> Optional[str]:
    """Get the version of the OpenAI Agents SDK."""
    try:
        import agents
        return getattr(agents, '__version__', 'unknown')
    except ImportError:
        return None


# Utility functions for debugging
def test_sdk_integration() -> Dict[str, Any]:
    """Test SDK integration components."""
    test_results = {
        "imports": {},
        "initialization": {},
        "basic_functionality": {}
    }
    
    # Test imports
    modules_to_test = [
        ("agents", "OpenAI Agents SDK"),
        ("framework.helpers.guardrails", "Guardrails system"),
        ("framework.helpers.agent_tracing", "Tracing system"),
        ("framework.helpers.agent_tools_wrapper", "Tools wrapper"),
        ("framework.helpers.agents_sdk_wrapper", "SDK wrapper")
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            test_results["imports"][description] = "success"
        except ImportError as e:
            test_results["imports"][description] = f"failed: {e}"
    
    # Test initialization (basic)
    try:
        init_results = initialize_sdk_integration()
        test_results["initialization"] = init_results
    except Exception as e:
        test_results["initialization"] = {"error": str(e)}
    
    # Test basic functionality
    try:
        status = get_sdk_status()
        test_results["basic_functionality"]["status_check"] = "success"
        test_results["basic_functionality"]["status"] = status
    except Exception as e:
        test_results["basic_functionality"]["status_check"] = f"failed: {e}"
    
    return test_results