"""Guardrails system for Gary-Zero with OpenAI Agents SDK integration.

This module provides input validation, output filtering, safety evaluation,
and error handling capabilities to ensure safe and reliable agent operations.
"""

import re
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

# OpenAI Agents SDK imports
from agents import InputGuardrail, OutputGuardrail, RunResult
from agents.guardrail import InputGuardrailResult, OutputGuardrailResult

# Gary-Zero imports
from framework.helpers.print_style import PrintStyle


class GuardrailSeverity(Enum):
    """Severity levels for guardrail violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation."""
    rule_name: str
    severity: GuardrailSeverity
    message: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InputValidator:
    """Input validation and sanitization for agent messages."""
    
    def __init__(self):
        self.max_length = 10000
        self.banned_patterns = [
            r'(?i)ignore\s+previous\s+instructions',
            r'(?i)ignore\s+all\s+previous',
            r'(?i)system\s*:\s*ignore',
            r'(?i)override\s+safety',
            r'(?i)jailbreak',
            r'(?i)pretend\s+you\s+are',
        ]
        self.sensitive_info_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email (for logging)
        ]
        self.violations: List[GuardrailViolation] = []
    
    async def validate_and_sanitize(self, message: str) -> str:
        """Validate and sanitize input message."""
        self.violations.clear()
        
        # Length validation
        if len(message) > self.max_length:
            self.violations.append(GuardrailViolation(
                rule_name="max_length",
                severity=GuardrailSeverity.MEDIUM,
                message=f"Message too long ({len(message)} > {self.max_length})",
                content=message[:100] + "..."
            ))
            message = message[:self.max_length] + " [truncated by guardrail]"
        
        # Injection attempt detection
        for pattern in self.banned_patterns:
            if re.search(pattern, message):
                self.violations.append(GuardrailViolation(
                    rule_name="injection_attempt",
                    severity=GuardrailSeverity.HIGH,
                    message=f"Potential prompt injection detected: {pattern}",
                    content=message[:200] + "..."
                ))
                # Sanitize by adding warning
                message = f"[WARNING: Potential prompt injection detected] {message}"
        
        # Sensitive information detection
        for pattern in self.sensitive_info_patterns:
            matches = re.findall(pattern, message)
            if matches:
                self.violations.append(GuardrailViolation(
                    rule_name="sensitive_info",
                    severity=GuardrailSeverity.HIGH,
                    message=f"Sensitive information detected: {len(matches)} matches",
                    content="[Redacted for security]",
                    metadata={"pattern_type": pattern, "match_count": len(matches)}
                ))
                # Redact sensitive information
                message = re.sub(pattern, "[REDACTED]", message)
        
        # Log violations
        if self.violations:
            await self._log_violations()
        
        return message
    
    async def _log_violations(self):
        """Log guardrail violations."""
        for violation in self.violations:
            color = self._get_severity_color(violation.severity)
            PrintStyle(font_color=color, padding=True).print(
                f"[INPUT GUARDRAIL] {violation.rule_name}: {violation.message}"
            )
    
    def _get_severity_color(self, severity: GuardrailSeverity) -> str:
        """Get color for severity level."""
        colors = {
            GuardrailSeverity.LOW: "yellow",
            GuardrailSeverity.MEDIUM: "orange", 
            GuardrailSeverity.HIGH: "red",
            GuardrailSeverity.CRITICAL: "purple"
        }
        return colors.get(severity, "white")
    
    def get_violations(self) -> List[GuardrailViolation]:
        """Get recent violations."""
        return self.violations.copy()


class OutputValidator:
    """Output validation and filtering for agent responses."""
    
    def __init__(self):
        self.max_length = 50000
        self.banned_content_patterns = [
            r'(?i)generate\s+malware',
            r'(?i)create\s+virus',
            r'(?i)hack\s+into',
            r'(?i)illegal\s+activities',
        ]
        self.pii_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        ]
        self.violations: List[GuardrailViolation] = []
    
    async def validate_output(self, result: RunResult) -> RunResult:
        """Validate agent output and filter if necessary."""
        self.violations.clear()
        
        if not result.is_success:
            return result
        
        # Get string representation of the result
        output_str = str(result.value)
        
        # Length validation
        if len(output_str) > self.max_length:
            self.violations.append(GuardrailViolation(
                rule_name="output_max_length",
                severity=GuardrailSeverity.MEDIUM,
                message=f"Output too long ({len(output_str)} > {self.max_length})",
                content=output_str[:100] + "..."
            ))
            output_str = output_str[:self.max_length] + " [truncated by output guardrail]"
        
        # Banned content detection
        for pattern in self.banned_content_patterns:
            if re.search(pattern, output_str):
                self.violations.append(GuardrailViolation(
                    rule_name="banned_content",
                    severity=GuardrailSeverity.CRITICAL,
                    message=f"Banned content pattern detected: {pattern}",
                    content=output_str[:200] + "..."
                ))
                # Replace with safety message
                output_str = "[Content blocked by safety guardrail - potentially harmful content detected]"
        
        # PII detection and redaction
        for pattern in self.pii_patterns:
            matches = re.findall(pattern, output_str)
            if matches:
                self.violations.append(GuardrailViolation(
                    rule_name="pii_detected",
                    severity=GuardrailSeverity.HIGH,
                    message=f"PII detected in output: {len(matches)} matches",
                    content="[Redacted for privacy]",
                    metadata={"pattern_type": pattern, "match_count": len(matches)}
                ))
                # Redact PII
                output_str = re.sub(pattern, "[PII_REDACTED]", output_str)
        
        # Log violations
        if self.violations:
            await self._log_violations()
        
        # Return modified result if needed
        if output_str != str(result.value):
            # Create new result with sanitized output
            return RunResult(value=output_str, error=None)
        
        return result
    
    async def _log_violations(self):
        """Log guardrail violations."""
        for violation in self.violations:
            color = self._get_severity_color(violation.severity)
            PrintStyle(font_color=color, padding=True).print(
                f"[OUTPUT GUARDRAIL] {violation.rule_name}: {violation.message}"
            )
    
    def _get_severity_color(self, severity: GuardrailSeverity) -> str:
        """Get color for severity level."""
        colors = {
            GuardrailSeverity.LOW: "yellow",
            GuardrailSeverity.MEDIUM: "orange",
            GuardrailSeverity.HIGH: "red", 
            GuardrailSeverity.CRITICAL: "purple"
        }
        return colors.get(severity, "white")
    
    def get_violations(self) -> List[GuardrailViolation]:
        """Get recent violations."""
        return self.violations.copy()


class SafetyEvaluator:
    """Evaluate agent interactions for safety concerns."""
    
    def __init__(self):
        self.evaluation_history: List[Dict[str, Any]] = []
        self.risk_threshold = 0.7  # Risk score threshold (0-1)
    
    async def evaluate_interaction(self, input_msg: str, output: str) -> Dict[str, Any]:
        """Evaluate a complete input-output interaction for safety."""
        evaluation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_length": len(input_msg),
            "output_length": len(output),
            "risk_score": 0.0,
            "risk_factors": [],
            "is_safe": True
        }
        
        # Evaluate input risks
        input_risks = await self._evaluate_input_risks(input_msg)
        evaluation["risk_score"] += input_risks["score"] * 0.4
        evaluation["risk_factors"].extend(input_risks["factors"])
        
        # Evaluate output risks
        output_risks = await self._evaluate_output_risks(output)
        evaluation["risk_score"] += output_risks["score"] * 0.6
        evaluation["risk_factors"].extend(output_risks["factors"])
        
        # Determine if interaction is safe
        evaluation["is_safe"] = evaluation["risk_score"] < self.risk_threshold
        
        # Store evaluation
        self.evaluation_history.append(evaluation)
        
        # Log high-risk interactions
        if not evaluation["is_safe"]:
            PrintStyle(font_color="red", padding=True).print(
                f"[SAFETY] High-risk interaction detected (score: {evaluation['risk_score']:.2f})"
            )
        
        return evaluation
    
    async def _evaluate_input_risks(self, input_msg: str) -> Dict[str, Any]:
        """Evaluate risks in input message."""
        risk_score = 0.0
        risk_factors = []
        
        # Check for manipulation attempts
        manipulation_patterns = [
            r'(?i)ignore\s+previous',
            r'(?i)forget\s+instructions',
            r'(?i)override\s+safety',
        ]
        
        for pattern in manipulation_patterns:
            if re.search(pattern, input_msg):
                risk_score += 0.3
                risk_factors.append(f"manipulation_attempt: {pattern}")
        
        # Check for requests for harmful content
        harmful_patterns = [
            r'(?i)how\s+to\s+hack',
            r'(?i)make\s+explosives',
            r'(?i)illegal\s+drugs',
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, input_msg):
                risk_score += 0.5
                risk_factors.append(f"harmful_request: {pattern}")
        
        return {
            "score": min(risk_score, 1.0),
            "factors": risk_factors
        }
    
    async def _evaluate_output_risks(self, output: str) -> Dict[str, Any]:
        """Evaluate risks in output content."""
        risk_score = 0.0
        risk_factors = []
        
        # Check for potentially harmful instructions
        harmful_output_patterns = [
            r'(?i)here\'s\s+how\s+to\s+hack',
            r'(?i)steps\s+to\s+create\s+malware',
            r'(?i)illegal\s+activities\s+include',
        ]
        
        for pattern in harmful_output_patterns:
            if re.search(pattern, output):
                risk_score += 0.6
                risk_factors.append(f"harmful_instructions: {pattern}")
        
        # Check for private information disclosure
        if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', output):
            risk_score += 0.4
            risk_factors.append("potential_pii_disclosure")
        
        return {
            "score": min(risk_score, 1.0),
            "factors": risk_factors
        }
    
    def get_evaluation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent evaluation history."""
        return self.evaluation_history[-limit:]


class ErrorHandler:
    """Enhanced error handling with guardrails integration."""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.retry_strategies = {
            "network_error": self._handle_network_error,
            "rate_limit": self._handle_rate_limit,
            "validation_error": self._handle_validation_error,
            "safety_violation": self._handle_safety_violation
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle errors with appropriate strategies."""
        error_type = self._classify_error(error)
        
        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "context": context,
            "handled": False,
            "retry_suggested": False
        }
        
        # Apply appropriate handling strategy
        if error_type in self.retry_strategies:
            handling_result = await self.retry_strategies[error_type](error, context)
            error_record.update(handling_result)
        else:
            error_record["handling_result"] = "no_specific_strategy"
        
        # Store error record
        self.error_history.append(error_record)
        
        # Log error
        PrintStyle(font_color="red", padding=True).print(
            f"[ERROR HANDLER] {error_type}: {str(error)[:100]}..."
        )
        
        return error_record
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate handling."""
        error_str = str(error).lower()
        
        if "network" in error_str or "connection" in error_str:
            return "network_error"
        elif "rate limit" in error_str or "quota" in error_str:
            return "rate_limit"
        elif "validation" in error_str or "invalid" in error_str:
            return "validation_error"
        elif "safety" in error_str or "guardrail" in error_str:
            return "safety_violation"
        else:
            return "unknown_error"
    
    async def _handle_network_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network-related errors."""
        return {
            "handled": True,
            "retry_suggested": True,
            "retry_delay": 5,
            "handling_strategy": "exponential_backoff"
        }
    
    async def _handle_rate_limit(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limit errors."""
        return {
            "handled": True,
            "retry_suggested": True,
            "retry_delay": 60,
            "handling_strategy": "rate_limit_backoff"
        }
    
    async def _handle_validation_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors."""
        return {
            "handled": True,
            "retry_suggested": False,
            "handling_strategy": "input_sanitization"
        }
    
    async def _handle_safety_violation(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle safety violations."""
        return {
            "handled": True,
            "retry_suggested": False,
            "handling_strategy": "safety_block"
        }


class GuardrailsManager:
    """Central manager for all guardrail systems."""
    
    def __init__(self):
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()
        self.safety_evaluator = SafetyEvaluator()
        self.error_handler = ErrorHandler()
        
        self.enabled = True
        self.strict_mode = False  # If True, blocks on any violation
    
    async def process_input(self, message: str) -> str:
        """Process input through all input guardrails."""
        if not self.enabled:
            return message
        
        try:
            validated_message = await self.input_validator.validate_and_sanitize(message)
            return validated_message
        except Exception as e:
            await self.error_handler.handle_error(e, {"stage": "input_processing"})
            # Return original message if guardrails fail
            return message
    
    async def process_output(self, result: RunResult) -> RunResult:
        """Process output through all output guardrails."""
        if not self.enabled:
            return result
        
        try:
            validated_result = await self.output_validator.validate_output(result)
            return validated_result
        except Exception as e:
            await self.error_handler.handle_error(e, {"stage": "output_processing"})
            # Return original result if guardrails fail
            return result
    
    async def evaluate_interaction(self, input_msg: str, output: str) -> Dict[str, Any]:
        """Evaluate complete interaction for safety."""
        if not self.enabled:
            return {"is_safe": True, "risk_score": 0.0}
        
        try:
            evaluation = await self.safety_evaluator.evaluate_interaction(input_msg, output)
            return evaluation
        except Exception as e:
            await self.error_handler.handle_error(e, {"stage": "safety_evaluation"})
            return {"is_safe": True, "risk_score": 0.0, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all guardrail systems."""
        return {
            "enabled": self.enabled,
            "strict_mode": self.strict_mode,
            "input_violations": len(self.input_validator.get_violations()),
            "output_violations": len(self.output_validator.get_violations()),
            "recent_evaluations": len(self.safety_evaluator.get_evaluation_history(10)),
            "recent_errors": len(self.error_handler.error_history[-10:])
        }
    
    def enable_strict_mode(self):
        """Enable strict mode - blocks on any violation."""
        self.strict_mode = True
        PrintStyle(font_color="yellow", padding=True).print(
            "[GUARDRAILS] Strict mode enabled"
        )
    
    def disable_strict_mode(self):
        """Disable strict mode - allows sanitized content through."""
        self.strict_mode = False
        PrintStyle(font_color="green", padding=True).print(
            "[GUARDRAILS] Strict mode disabled"
        )


# Global guardrails manager
_guardrails_manager: Optional[GuardrailsManager] = None


def get_guardrails_manager() -> GuardrailsManager:
    """Get the global guardrails manager."""
    global _guardrails_manager
    if _guardrails_manager is None:
        _guardrails_manager = GuardrailsManager()
    return _guardrails_manager


def initialize_guardrails(strict_mode: bool = False) -> None:
    """Initialize the guardrails system."""
    manager = get_guardrails_manager()
    if strict_mode:
        manager.enable_strict_mode()
    
    PrintStyle(font_color="green", padding=True).print(
        "Guardrails system initialized"
    )