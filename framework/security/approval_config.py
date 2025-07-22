"""
Configuration management for approval workflows.

This module provides APIs for managing approval policies, user roles,
and workflow settings at runtime.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from .approval_workflow import (
    ApprovalWorkflow, ActionDefinition, RiskLevel, 
    ApprovalPolicy, UserRole
)


class ApprovalConfigManager:
    """Manager for approval workflow configuration."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else Path("approval_config.json")
        self.workflow: Optional[ApprovalWorkflow] = None
        
        # Default configuration
        self.default_config = {
            "global_settings": {
                "default_timeout": 300,
                "max_pending_requests": 100,
                "cache_duration": 3600,
                "enable_approval_logs": True
            },
            "user_roles": {},
            "action_policies": {},
            "role_permissions": {
                "owner": ["file_write", "file_delete", "shell_command", "external_api_call", 
                         "computer_control", "code_execution", "payment_transaction", "config_change"],
                "admin": ["file_write", "file_delete", "shell_command", "external_api_call", 
                         "code_execution", "config_change"],
                "user": ["file_write", "external_api_call", "config_change"],
                "guest": [],
                "subordinate_agent": []
            }
        }
    
    def set_workflow(self, workflow: ApprovalWorkflow) -> None:
        """Set the approval workflow instance to manage."""
        self.workflow = workflow
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                return self._merge_config(self.default_config, config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_file}: {e}")
        
        return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config file {self.config_file}: {e}")
            return False
    
    def apply_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Apply configuration to the workflow."""
        if not self.workflow:
            raise ValueError("No workflow instance set")
        
        if config is None:
            config = self.load_config()
        
        try:
            # Apply global settings
            global_settings = config.get("global_settings", {})
            self.workflow.global_timeout = global_settings.get("default_timeout", 300)
            self.workflow.max_pending_requests = global_settings.get("max_pending_requests", 100)
            self.workflow.cache_duration = global_settings.get("cache_duration", 3600)
            
            # Apply user roles
            user_roles = config.get("user_roles", {})
            for user_id, role_name in user_roles.items():
                try:
                    role = UserRole(role_name)
                    self.workflow.set_user_role(user_id, role)
                except ValueError:
                    print(f"Warning: Invalid role '{role_name}' for user {user_id}")
            
            # Apply action policies
            action_policies = config.get("action_policies", {})
            for action_type, policy_config in action_policies.items():
                if action_type in self.workflow.action_definitions:
                    try:
                        if "approval_policy" in policy_config:
                            policy = ApprovalPolicy(policy_config["approval_policy"])
                            self.workflow.configure_action(action_type, approval_policy=policy)
                        
                        if "timeout_seconds" in policy_config:
                            self.workflow.configure_action(
                                action_type, 
                                timeout_seconds=policy_config["timeout_seconds"]
                            )
                        
                        if "required_roles" in policy_config:
                            roles = [UserRole(r) for r in policy_config["required_roles"]]
                            self.workflow.configure_action(action_type, required_roles=roles)
                            
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Invalid policy config for action {action_type}: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error applying configuration: {e}")
            return False
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration from the workflow."""
        if not self.workflow:
            return self.default_config.copy()
        
        config = {
            "global_settings": {
                "default_timeout": self.workflow.global_timeout,
                "max_pending_requests": self.workflow.max_pending_requests,
                "cache_duration": self.workflow.cache_duration,
                "enable_approval_logs": True
            },
            "user_roles": {
                user_id: role.value 
                for user_id, role in self.workflow.user_roles.items()
            },
            "action_policies": {},
            "role_permissions": self.default_config["role_permissions"].copy()
        }
        
        # Export action definitions
        for action_type, action_def in self.workflow.action_definitions.items():
            config["action_policies"][action_type] = {
                "risk_level": action_def.risk_level.value,
                "approval_policy": action_def.approval_policy.value,
                "timeout_seconds": action_def.timeout_seconds,
                "required_roles": [role.value for role in action_def.required_roles],
                "description": action_def.description
            }
        
        return config
    
    def update_user_role(self, user_id: str, role: str) -> bool:
        """Update user role and save configuration."""
        try:
            role_enum = UserRole(role)
            if self.workflow:
                self.workflow.set_user_role(user_id, role_enum)
            
            # Update config file
            config = self.load_config()
            config["user_roles"][user_id] = role
            return self.save_config(config)
            
        except ValueError:
            return False
    
    def update_action_policy(self, action_type: str, **policy_updates) -> bool:
        """Update action policy and save configuration."""
        try:
            if self.workflow and action_type in self.workflow.action_definitions:
                # Apply to workflow
                valid_updates = {}
                
                if "approval_policy" in policy_updates:
                    policy = ApprovalPolicy(policy_updates["approval_policy"])
                    valid_updates["approval_policy"] = policy
                
                if "timeout_seconds" in policy_updates:
                    valid_updates["timeout_seconds"] = int(policy_updates["timeout_seconds"])
                
                if "required_roles" in policy_updates:
                    roles = [UserRole(r) for r in policy_updates["required_roles"]]
                    valid_updates["required_roles"] = roles
                
                self.workflow.configure_action(action_type, **valid_updates)
            
            # Update config file
            config = self.load_config()
            if action_type not in config["action_policies"]:
                config["action_policies"][action_type] = {}
            
            config["action_policies"][action_type].update(policy_updates)
            return self.save_config(config)
            
        except (ValueError, KeyError) as e:
            print(f"Error updating action policy: {e}")
            return False
    
    def register_custom_action(self, action_definition: Dict[str, Any]) -> bool:
        """Register a new custom action type."""
        try:
            action_def = ActionDefinition(
                action_type=action_definition["action_type"],
                risk_level=RiskLevel(action_definition["risk_level"]),
                description=action_definition["description"],
                required_roles=[UserRole(r) for r in action_definition["required_roles"]],
                approval_policy=ApprovalPolicy(action_definition.get("approval_policy", "always_ask")),
                timeout_seconds=action_definition.get("timeout_seconds", 300)
            )
            
            if self.workflow:
                self.workflow.register_action(action_def)
            
            # Update config file
            config = self.load_config()
            config["action_policies"][action_def.action_type] = {
                "risk_level": action_def.risk_level.value,
                "approval_policy": action_def.approval_policy.value,
                "timeout_seconds": action_def.timeout_seconds,
                "required_roles": [role.value for role in action_def.required_roles],
                "description": action_def.description
            }
            
            return self.save_config(config)
            
        except (ValueError, KeyError) as e:
            print(f"Error registering custom action: {e}")
            return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """Get list of actions a user is permitted to perform."""
        if not self.workflow:
            return []
        
        user_role = self.workflow.get_user_role(user_id)
        permitted_actions = []
        
        for action_type, action_def in self.workflow.action_definitions.items():
            if user_role in action_def.required_roles:
                permitted_actions.append(action_type)
        
        return permitted_actions
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate user roles
        user_roles = config.get("user_roles", {})
        for user_id, role_name in user_roles.items():
            try:
                UserRole(role_name)
            except ValueError:
                errors.append(f"Invalid role '{role_name}' for user {user_id}")
        
        # Validate action policies
        action_policies = config.get("action_policies", {})
        for action_type, policy_config in action_policies.items():
            if "approval_policy" in policy_config:
                try:
                    ApprovalPolicy(policy_config["approval_policy"])
                except ValueError:
                    errors.append(f"Invalid approval policy for action {action_type}")
            
            if "risk_level" in policy_config:
                try:
                    RiskLevel(policy_config["risk_level"])
                except ValueError:
                    errors.append(f"Invalid risk level for action {action_type}")
            
            if "required_roles" in policy_config:
                for role_name in policy_config["required_roles"]:
                    try:
                        UserRole(role_name)
                    except ValueError:
                        errors.append(f"Invalid required role '{role_name}' for action {action_type}")
        
        return errors
    
    def export_config_template(self, file_path: str) -> bool:
        """Export a configuration template with all available options."""
        template = {
            "global_settings": {
                "default_timeout": 300,
                "max_pending_requests": 100,
                "cache_duration": 3600,
                "enable_approval_logs": True
            },
            "user_roles": {
                "admin_user": "admin",
                "regular_user": "user",
                "guest_user": "guest"
            },
            "action_policies": {
                "file_write": {
                    "approval_policy": "ask_once",
                    "timeout_seconds": 120,
                    "required_roles": ["owner", "admin", "user"]
                },
                "file_delete": {
                    "approval_policy": "always_ask",
                    "timeout_seconds": 300,
                    "required_roles": ["owner", "admin"]
                },
                "shell_command": {
                    "approval_policy": "always_ask",
                    "timeout_seconds": 180,
                    "required_roles": ["owner", "admin"]
                }
            },
            "_comments": {
                "approval_policies": ["always_ask", "ask_once", "never_ask", "role_based"],
                "risk_levels": ["low", "medium", "high", "critical"],
                "user_roles": ["owner", "admin", "user", "guest", "subordinate_agent"]
            }
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(template, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting template: {e}")
            return False
    
    def _merge_config(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries."""
        merged = default.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged


# Global configuration manager instance
_config_manager: Optional[ApprovalConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ApprovalConfigManager:
    """Get or create the global configuration manager."""
    global _config_manager
    if _config_manager is None or config_file:
        _config_manager = ApprovalConfigManager(config_file)
    return _config_manager


def setup_approval_workflow_from_config(
    config_file: Optional[str] = None,
    workflow: Optional[ApprovalWorkflow] = None
) -> ApprovalWorkflow:
    """Setup and configure an approval workflow from configuration file."""
    config_manager = get_config_manager(config_file)
    
    if workflow is None:
        from .audit_logger import AuditLogger
        workflow = ApprovalWorkflow(AuditLogger())
    
    config_manager.set_workflow(workflow)
    config_manager.apply_config()
    
    return workflow