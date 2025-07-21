"""Quality control and review system for Gary Zero agent.

This module provides automated quality assessment, code review,
and output validation mechanisms to ensure high-quality results.
"""

import ast
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass


class QualityLevel(Enum):
    """Quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNACCEPTABLE = "unacceptable"


class ReviewType(Enum):
    """Types of reviews that can be performed."""
    CODE_REVIEW = "code_review"
    OUTPUT_VALIDATION = "output_validation"
    TASK_COMPLETION = "task_completion"
    RESPONSE_QUALITY = "response_quality"
    SECURITY_AUDIT = "security_audit"


@dataclass
class QualityMetric:
    """Individual quality metric assessment."""
    name: str
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    description: str = ""
    details: Dict[str, Any] = None


@dataclass
class QualityAssessment:
    """Complete quality assessment result."""
    overall_score: float
    quality_level: QualityLevel
    metrics: List[QualityMetric]
    timestamp: datetime
    review_type: ReviewType
    content_type: str
    recommendations: List[str]
    issues: List[str]
    passed_checks: List[str]


class QualityController:
    """Main quality control system."""
    
    def __init__(self):
        """Initialize the quality controller."""
        self.assessment_history: List[QualityAssessment] = []
        
        # Quality thresholds
        self.thresholds = {
            QualityLevel.EXCELLENT: 0.9,
            QualityLevel.GOOD: 0.75,
            QualityLevel.ACCEPTABLE: 0.6,
            QualityLevel.POOR: 0.4,
            QualityLevel.UNACCEPTABLE: 0.0
        }
    
    def assess_code_quality(self, code: str, language: str = "python") -> QualityAssessment:
        """Assess the quality of code output."""
        metrics = []
        
        if language.lower() == "python":
            metrics.extend(self._assess_python_code(code))
        elif language.lower() in ["javascript", "js"]:
            metrics.extend(self._assess_javascript_code(code))
        else:
            metrics.extend(self._assess_generic_code(code))
        
        # Calculate overall score
        if metrics:
            weighted_sum = sum(metric.score * metric.weight for metric in metrics)
            total_weight = sum(metric.weight for metric in metrics)
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.5  # Neutral score if no metrics
        
        quality_level = self._score_to_quality_level(overall_score)
        
        # Generate recommendations and issues
        recommendations = self._generate_code_recommendations(metrics, language)
        issues = self._identify_code_issues(metrics)
        passed_checks = self._identify_passed_checks(metrics)
        
        assessment = QualityAssessment(
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc),
            review_type=ReviewType.CODE_REVIEW,
            content_type=f"{language}_code",
            recommendations=recommendations,
            issues=issues,
            passed_checks=passed_checks
        )
        
        self.assessment_history.append(assessment)
        return assessment
    
    def assess_response_quality(self, response: str, context: str = "") -> QualityAssessment:
        """Assess the quality of an agent response."""
        metrics = []
        
        # Length and completeness
        metrics.append(self._assess_response_length(response))
        
        # Clarity and structure
        metrics.append(self._assess_response_clarity(response))
        
        # Relevance to context
        if context:
            metrics.append(self._assess_response_relevance(response, context))
        
        # Helpfulness indicators
        metrics.append(self._assess_response_helpfulness(response))
        
        # Professional tone
        metrics.append(self._assess_response_tone(response))
        
        # Calculate overall score
        weighted_sum = sum(metric.score * metric.weight for metric in metrics)
        total_weight = sum(metric.weight for metric in metrics)
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        quality_level = self._score_to_quality_level(overall_score)
        
        recommendations = self._generate_response_recommendations(metrics)
        issues = self._identify_response_issues(metrics)
        passed_checks = self._identify_passed_checks(metrics)
        
        assessment = QualityAssessment(
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc),
            review_type=ReviewType.RESPONSE_QUALITY,
            content_type="text_response",
            recommendations=recommendations,
            issues=issues,
            passed_checks=passed_checks
        )
        
        self.assessment_history.append(assessment)
        return assessment
    
    def assess_task_completion(self, task_description: str, result: str) -> QualityAssessment:
        """Assess how well a task was completed."""
        metrics = []
        
        # Completeness - does the result address all parts of the task?
        metrics.append(self._assess_task_completeness(task_description, result))
        
        # Accuracy - is the result correct and factual?
        metrics.append(self._assess_result_accuracy(result))
        
        # Specificity - is the result specific enough?
        metrics.append(self._assess_result_specificity(result))
        
        # Actionability - can the user act on this result?
        metrics.append(self._assess_result_actionability(result))
        
        # Calculate overall score
        weighted_sum = sum(metric.score * metric.weight for metric in metrics)
        total_weight = sum(metric.weight for metric in metrics)
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        quality_level = self._score_to_quality_level(overall_score)
        
        recommendations = self._generate_task_recommendations(metrics)
        issues = self._identify_task_issues(metrics)
        passed_checks = self._identify_passed_checks(metrics)
        
        assessment = QualityAssessment(
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            timestamp=datetime.now(timezone.utc),
            review_type=ReviewType.TASK_COMPLETION,
            content_type="task_result",
            recommendations=recommendations,
            issues=issues,
            passed_checks=passed_checks
        )
        
        self.assessment_history.append(assessment)
        return assessment
    
    def _assess_python_code(self, code: str) -> List[QualityMetric]:
        """Assess Python code quality."""
        metrics = []
        
        # Syntax validity
        try:
            ast.parse(code)
            syntax_score = 1.0
            syntax_details = {"valid": True}
        except SyntaxError as e:
            syntax_score = 0.0
            syntax_details = {"valid": False, "error": str(e)}
        
        metrics.append(QualityMetric(
            name="syntax_validity",
            score=syntax_score,
            weight=2.0,
            description="Code syntax is valid",
            details=syntax_details
        ))
        
        # Code structure and formatting
        structure_score = self._assess_code_structure(code)
        metrics.append(QualityMetric(
            name="code_structure",
            score=structure_score,
            weight=1.5,
            description="Code is well-structured and formatted"
        ))
        
        # Documentation and comments
        doc_score = self._assess_code_documentation(code)
        metrics.append(QualityMetric(
            name="documentation",
            score=doc_score,
            weight=1.0,
            description="Code includes appropriate documentation"
        ))
        
        # Security considerations
        security_score = self._assess_code_security(code)
        metrics.append(QualityMetric(
            name="security",
            score=security_score,
            weight=1.5,
            description="Code follows security best practices"
        ))
        
        return metrics
    
    def _assess_javascript_code(self, code: str) -> List[QualityMetric]:
        """Assess JavaScript code quality."""
        metrics = []
        
        # Basic syntax checks (simplified)
        syntax_score = self._basic_js_syntax_check(code)
        metrics.append(QualityMetric(
            name="syntax_validity",
            score=syntax_score,
            weight=2.0,
            description="JavaScript syntax appears valid"
        ))
        
        # Code structure
        structure_score = self._assess_code_structure(code)
        metrics.append(QualityMetric(
            name="code_structure",
            score=structure_score,
            weight=1.5,
            description="Code is well-structured"
        ))
        
        return metrics
    
    def _assess_generic_code(self, code: str) -> List[QualityMetric]:
        """Assess generic code quality."""
        metrics = []
        
        # Basic structure assessment
        structure_score = self._assess_code_structure(code)
        metrics.append(QualityMetric(
            name="code_structure",
            score=structure_score,
            weight=1.0,
            description="Code appears well-structured"
        ))
        
        return metrics
    
    def _assess_code_structure(self, code: str) -> float:
        """Assess code structure and formatting."""
        score = 0.5  # Base score
        
        # Check for proper indentation
        lines = code.split('\n')
        indented_lines = sum(1 for line in lines if line.startswith(('    ', '\t')) and line.strip())
        if indented_lines > len(lines) * 0.2:  # At least 20% indented
            score += 0.2
        
        # Check for reasonable line length
        long_lines = sum(1 for line in lines if len(line) > 120)
        if long_lines < len(lines) * 0.1:  # Less than 10% long lines
            score += 0.1
        
        # Check for empty lines (good formatting)
        empty_lines = sum(1 for line in lines if not line.strip())
        if 0.05 < empty_lines / len(lines) < 0.3:  # Reasonable amount of whitespace
            score += 0.1
        
        # Check for consistent naming (basic check)
        if re.search(r'[a-z_][a-z0-9_]*', code):  # Snake_case or camelCase patterns
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_code_documentation(self, code: str) -> float:
        """Assess code documentation quality."""
        score = 0.0
        
        # Check for docstrings
        if '"""' in code or "'''" in code:
            score += 0.4
        
        # Check for comments
        comment_lines = len([line for line in code.split('\n') if line.strip().startswith('#')])
        total_lines = len([line for line in code.split('\n') if line.strip()])
        
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio > 0.1:  # At least 10% comments
                score += 0.3
            elif comment_ratio > 0.05:  # At least 5% comments
                score += 0.2
        
        # Check for function/class definitions with potential docs
        if re.search(r'def\s+\w+.*:\s*"""', code) or re.search(r'class\s+\w+.*:\s*"""', code):
            score += 0.3
        
        return min(1.0, score)
    
    def _assess_code_security(self, code: str) -> float:
        """Assess code security considerations."""
        score = 1.0  # Start optimistic
        
        # Check for common security issues
        security_issues = [
            r'eval\s*\(',  # eval() usage
            r'exec\s*\(',  # exec() usage
            r'__import__\s*\(',  # dynamic imports
            r'os\.system\s*\(',  # os.system() usage
            r'subprocess\.(call|run|Popen).*shell\s*=\s*True',  # shell=True
        ]
        
        for pattern in security_issues:
            if re.search(pattern, code, re.IGNORECASE):
                score -= 0.2
        
        return max(0.0, score)
    
    def _basic_js_syntax_check(self, code: str) -> float:
        """Basic JavaScript syntax validation."""
        # Very basic checks for common syntax errors
        balanced_braces = code.count('{') == code.count('}')
        balanced_parens = code.count('(') == code.count(')')
        balanced_brackets = code.count('[') == code.count(']')
        
        checks_passed = sum([balanced_braces, balanced_parens, balanced_brackets])
        return checks_passed / 3.0
    
    def _assess_response_length(self, response: str) -> QualityMetric:
        """Assess if response length is appropriate."""
        length = len(response.strip())
        
        if length < 20:
            score = 0.2  # Too short
        elif length < 50:
            score = 0.5  # Quite short
        elif length < 2000:
            score = 1.0  # Good length
        elif length < 5000:
            score = 0.8  # Getting long
        else:
            score = 0.6  # Very long
        
        return QualityMetric(
            name="response_length",
            score=score,
            weight=0.5,
            description="Response length is appropriate",
            details={"character_count": length}
        )
    
    def _assess_response_clarity(self, response: str) -> QualityMetric:
        """Assess response clarity and structure."""
        score = 0.5  # Base score
        
        # Check for structured content
        if any(marker in response for marker in ['1.', '2.', '-', '*', '##', '**']):
            score += 0.2
        
        # Check for reasonable sentence structure
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if 5 <= avg_sentence_length <= 25:  # Reasonable sentence length
            score += 0.2
        
        # Check for paragraphs
        if '\n\n' in response or response.count('\n') > 2:
            score += 0.1
        
        return QualityMetric(
            name="clarity_structure",
            score=min(1.0, score),
            weight=1.0,
            description="Response is clear and well-structured"
        )
    
    def _assess_response_relevance(self, response: str, context: str) -> QualityMetric:
        """Assess how relevant the response is to the context."""
        # Simple keyword overlap assessment
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())
        
        if context_words:
            overlap = len(response_words.intersection(context_words))
            relevance_score = min(1.0, overlap / (len(context_words) * 0.3))
        else:
            relevance_score = 0.5
        
        return QualityMetric(
            name="relevance",
            score=relevance_score,
            weight=1.5,
            description="Response is relevant to the context"
        )
    
    def _assess_response_helpfulness(self, response: str) -> QualityMetric:
        """Assess how helpful the response appears to be."""
        score = 0.5
        
        # Check for helpful patterns
        helpful_patterns = [
            r'here\s+(is|are)',
            r'you\s+can',
            r'try\s+this',
            r'example',
            r'step\s+\d',
            r'first.*second.*third',
            r'here\'s\s+how'
        ]
        
        for pattern in helpful_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                score += 0.1
        
        return QualityMetric(
            name="helpfulness",
            score=min(1.0, score),
            weight=1.0,
            description="Response appears helpful and actionable"
        )
    
    def _assess_response_tone(self, response: str) -> QualityMetric:
        """Assess the professional tone of the response."""
        score = 0.7  # Default professional score
        
        # Check for inappropriate content
        inappropriate_patterns = [
            r'\b(damn|hell|crap)\b',
            r'[!]{3,}',  # Multiple exclamation marks
            r'[A-Z]{5,}',  # ALL CAPS words
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, response):
                score -= 0.2
        
        # Check for positive indicators
        if any(word in response.lower() for word in ['please', 'thank', 'help', 'assist']):
            score += 0.1
        
        return QualityMetric(
            name="professional_tone",
            score=max(0.0, min(1.0, score)),
            weight=0.8,
            description="Response maintains professional tone"
        )
    
    def _assess_task_completeness(self, task: str, result: str) -> QualityMetric:
        """Assess how completely the task was addressed."""
        # Simple assessment based on response length relative to task complexity
        task_words = len(task.split())
        result_words = len(result.split())
        
        if task_words == 0:
            score = 0.5
        else:
            # Expect roughly 3-10 words of response per word of task
            ratio = result_words / task_words
            if 3 <= ratio <= 10:
                score = 1.0
            elif 1 <= ratio < 3:
                score = 0.7
            elif ratio < 1:
                score = 0.3
            else:  # ratio > 10
                score = 0.8  # Might be overly verbose but still complete
        
        return QualityMetric(
            name="task_completeness",
            score=score,
            weight=2.0,
            description="Task appears to be completely addressed"
        )
    
    def _assess_result_accuracy(self, result: str) -> QualityMetric:
        """Assess the apparent accuracy of the result."""
        # This is a simplified assessment - in practice would need domain-specific validation
        score = 0.8  # Default optimistic score
        
        # Check for uncertainty indicators (good for accuracy)
        uncertainty_patterns = [
            r'might\s+be',
            r'could\s+be',
            r'appears\s+to',
            r'seems\s+to',
            r'likely'
        ]
        
        uncertainty_count = sum(1 for pattern in uncertainty_patterns 
                               if re.search(pattern, result, re.IGNORECASE))
        
        # Some uncertainty is good (shows thoughtfulness)
        if 1 <= uncertainty_count <= 3:
            score += 0.1
        
        return QualityMetric(
            name="result_accuracy",
            score=min(1.0, score),
            weight=1.5,
            description="Result appears accurate and well-reasoned"
        )
    
    def _assess_result_specificity(self, result: str) -> QualityMetric:
        """Assess how specific and concrete the result is."""
        score = 0.5
        
        # Look for specific indicators
        specific_patterns = [
            r'\d+',  # Numbers
            r'step\s+\d',  # Step numbers
            r'line\s+\d',  # Line numbers
            r'version\s+\d',  # Version numbers
            r'[a-zA-Z]+\.[a-zA-Z]+',  # File extensions or methods
        ]
        
        for pattern in specific_patterns:
            if re.search(pattern, result):
                score += 0.1
        
        return QualityMetric(
            name="result_specificity",
            score=min(1.0, score),
            weight=1.0,
            description="Result is specific and concrete"
        )
    
    def _assess_result_actionability(self, result: str) -> QualityMetric:
        """Assess how actionable the result is."""
        score = 0.5
        
        # Look for actionable language
        actionable_patterns = [
            r'run\s+',
            r'execute\s+',
            r'click\s+',
            r'type\s+',
            r'install\s+',
            r'create\s+',
            r'open\s+',
            r'save\s+',
        ]
        
        for pattern in actionable_patterns:
            if re.search(pattern, result, re.IGNORECASE):
                score += 0.1
        
        return QualityMetric(
            name="result_actionability",
            score=min(1.0, score),
            weight=1.2,
            description="Result provides actionable guidance"
        )
    
    def _score_to_quality_level(self, score: float) -> QualityLevel:
        """Convert numeric score to quality level."""
        for level, threshold in sorted(self.thresholds.items(), 
                                       key=lambda x: x[1], reverse=True):
            if score >= threshold:
                return level
        return QualityLevel.UNACCEPTABLE
    
    def _generate_code_recommendations(self, metrics: List[QualityMetric], language: str) -> List[str]:
        """Generate recommendations for code improvement."""
        recommendations = []
        
        for metric in metrics:
            if metric.score < 0.7:
                if metric.name == "syntax_validity":
                    recommendations.append("Fix syntax errors before proceeding")
                elif metric.name == "code_structure":
                    recommendations.append("Improve code formatting and structure")
                elif metric.name == "documentation":
                    recommendations.append("Add more comments and documentation")
                elif metric.name == "security":
                    recommendations.append("Review code for security vulnerabilities")
        
        return recommendations
    
    def _generate_response_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Generate recommendations for response improvement."""
        recommendations = []
        
        for metric in metrics:
            if metric.score < 0.7:
                if metric.name == "response_length":
                    recommendations.append("Adjust response length - provide more detail or be more concise")
                elif metric.name == "clarity_structure":
                    recommendations.append("Improve response structure and clarity")
                elif metric.name == "relevance":
                    recommendations.append("Make response more relevant to the context")
                elif metric.name == "helpfulness":
                    recommendations.append("Provide more actionable and helpful information")
        
        return recommendations
    
    def _generate_task_recommendations(self, metrics: List[QualityMetric]) -> List[str]:
        """Generate recommendations for task completion improvement."""
        recommendations = []
        
        for metric in metrics:
            if metric.score < 0.7:
                if metric.name == "task_completeness":
                    recommendations.append("Address all aspects of the task more thoroughly")
                elif metric.name == "result_accuracy":
                    recommendations.append("Verify accuracy and provide more confident responses")
                elif metric.name == "result_specificity":
                    recommendations.append("Provide more specific and detailed information")
                elif metric.name == "result_actionability":
                    recommendations.append("Include more actionable steps and guidance")
        
        return recommendations
    
    def _identify_code_issues(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify issues in code quality."""
        issues = []
        
        for metric in metrics:
            if metric.score < 0.5:
                if metric.name == "syntax_validity":
                    issues.append("Code contains syntax errors")
                elif metric.name == "security":
                    issues.append("Code may have security vulnerabilities")
                elif metric.name == "code_structure":
                    issues.append("Code structure needs improvement")
        
        return issues
    
    def _identify_response_issues(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify issues in response quality."""
        issues = []
        
        for metric in metrics:
            if metric.score < 0.5:
                if metric.name == "relevance":
                    issues.append("Response not sufficiently relevant to context")
                elif metric.name == "professional_tone":
                    issues.append("Response tone could be more professional")
        
        return issues
    
    def _identify_task_issues(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify issues in task completion."""
        issues = []
        
        for metric in metrics:
            if metric.score < 0.5:
                if metric.name == "task_completeness":
                    issues.append("Task not fully completed")
                elif metric.name == "result_accuracy":
                    issues.append("Result accuracy is questionable")
        
        return issues
    
    def _identify_passed_checks(self, metrics: List[QualityMetric]) -> List[str]:
        """Identify checks that passed well."""
        passed = []
        
        for metric in metrics:
            if metric.score >= 0.8:
                passed.append(f"{metric.description}")
        
        return passed
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality control statistics."""
        if not self.assessment_history:
            return {"total_assessments": 0}
        
        total = len(self.assessment_history)
        
        # Quality level distribution
        level_counts = {}
        for level in QualityLevel:
            level_counts[level.value] = sum(1 for a in self.assessment_history if a.quality_level == level)
        
        # Review type distribution
        type_counts = {}
        for review_type in ReviewType:
            type_counts[review_type.value] = sum(1 for a in self.assessment_history if a.review_type == review_type)
        
        # Average scores
        avg_score = sum(a.overall_score for a in self.assessment_history) / total
        
        return {
            "total_assessments": total,
            "average_score": avg_score,
            "quality_distribution": level_counts,
            "review_type_distribution": type_counts,
            "latest_assessment": self.assessment_history[-1].overall_score if self.assessment_history else None
        }


# Global quality controller instance
_quality_controller: Optional[QualityController] = None


def get_quality_controller() -> QualityController:
    """Get the global quality controller instance."""
    global _quality_controller
    if _quality_controller is None:
        _quality_controller = QualityController()
    return _quality_controller