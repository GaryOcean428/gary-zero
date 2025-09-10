"""Advanced prompt engineering and template management system.

This module provides sophisticated prompt management capabilities including:
- Template management with versioning
- Dynamic prompt optimization
- A/B testing for prompts
- Performance analytics and optimization
- Context-aware prompt adaptation
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from jinja2 import Template, Environment, meta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of prompts."""
    
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    INSTRUCTION = "instruction"


class OptimizationStrategy(str, Enum):
    """Prompt optimization strategies."""
    
    LENGTH_REDUCTION = "length_reduction"
    CLARITY_IMPROVEMENT = "clarity_improvement"
    CONTEXT_ENHANCEMENT = "context_enhancement"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    COST_REDUCTION = "cost_reduction"


@dataclass
class PromptMetrics:
    """Metrics for prompt performance."""
    
    success_rate: float = 0.0
    average_response_time: float = 0.0
    average_cost: float = 0.0
    token_efficiency: float = 0.0  # Output tokens / Input tokens
    user_satisfaction: float = 0.0
    coherence_score: float = 0.0
    relevance_score: float = 0.0
    total_executions: int = 0


@dataclass
class PromptTemplate:
    """Prompt template with metadata."""
    
    id: str
    name: str
    description: str
    template: str
    prompt_type: PromptType
    version: str
    created_at: datetime
    updated_at: datetime
    variables: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metrics: PromptMetrics = field(default_factory=PromptMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render template with context variables."""
        try:
            jinja_template = Template(self.template)
            return jinja_template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {self.id}: {e}")
            return self.template
    
    def get_required_variables(self) -> List[str]:
        """Get list of required template variables."""
        env = Environment()
        parsed = env.parse(self.template)
        return list(meta.find_undeclared_variables(parsed))


class PromptOptimizer:
    """Optimizes prompts for performance and cost."""
    
    def __init__(self):
        self.optimization_rules = {
            OptimizationStrategy.LENGTH_REDUCTION: self._optimize_length,
            OptimizationStrategy.CLARITY_IMPROVEMENT: self._optimize_clarity,
            OptimizationStrategy.CONTEXT_ENHANCEMENT: self._optimize_context,
            OptimizationStrategy.PERFORMANCE_OPTIMIZATION: self._optimize_performance,
            OptimizationStrategy.COST_REDUCTION: self._optimize_cost,
        }
    
    async def optimize_prompt(
        self,
        prompt: str,
        strategy: OptimizationStrategy,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Optimize prompt using specified strategy."""
        optimizer_func = self.optimization_rules.get(strategy)
        if optimizer_func:
            return await optimizer_func(prompt, context or {})
        return prompt
    
    async def _optimize_length(self, prompt: str, context: Dict[str, Any]) -> str:
        """Reduce prompt length while maintaining meaning."""
        # Remove redundant phrases and words
        optimized = re.sub(r'\b(please|kindly|if you would)\b', '', prompt, flags=re.IGNORECASE)
        optimized = re.sub(r'\s+', ' ', optimized)  # Remove extra whitespace
        optimized = re.sub(r'([.!?])\s*\1+', r'\1', optimized)  # Remove duplicate punctuation
        return optimized.strip()
    
    async def _optimize_clarity(self, prompt: str, context: Dict[str, Any]) -> str:
        """Improve prompt clarity and structure."""
        # Add structure if missing
        if not any(marker in prompt for marker in ['1.', '2.', '-', '*']):
            # Simple optimization: add structure to instructions
            sentences = prompt.split('.')
            if len(sentences) > 2:
                structured = []
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        structured.append(f"{i+1}. {sentence.strip()}")
                return '. '.join(structured) + '.'
        return prompt
    
    async def _optimize_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with relevant context."""
        # Add context information if available
        if context.get('user_expertise'):
            expertise = context['user_expertise']
            if 'beginner' in expertise.lower() and 'explain' not in prompt.lower():
                prompt += " Please explain in simple terms."
            elif 'expert' in expertise.lower() and 'detailed' not in prompt.lower():
                prompt += " Provide detailed technical information."
        
        return prompt
    
    async def _optimize_performance(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize for model performance."""
        # Add specific instructions that typically improve performance
        if 'think' not in prompt.lower() and 'step' not in prompt.lower():
            prompt += " Think step by step."
        
        if '?' in prompt and 'answer' not in prompt.lower():
            prompt += " Provide a clear and direct answer."
        
        return prompt
    
    async def _optimize_cost(self, prompt: str, context: Dict[str, Any]) -> str:
        """Optimize for cost efficiency."""
        # Combine length reduction with performance optimization
        optimized = await self._optimize_length(prompt, context)
        
        # Remove examples if they're long and not essential
        if len(optimized) > 500 and 'example' in optimized.lower():
            # Simple example removal (would be more sophisticated in practice)
            lines = optimized.split('\n')
            filtered_lines = []
            skip_example = False
            
            for line in lines:
                if 'example' in line.lower():
                    skip_example = True
                    continue
                elif skip_example and (line.strip() == '' or line[0].isupper()):
                    skip_example = False
                
                if not skip_example:
                    filtered_lines.append(line)
            
            optimized = '\n'.join(filtered_lines)
        
        return optimized


class PromptManager:
    """Manages prompt templates and optimization."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("prompt_templates")
        self.storage_path.mkdir(exist_ok=True)
        self.templates: Dict[str, PromptTemplate] = {}
        self.versions: Dict[str, List[PromptTemplate]] = {}
        self.optimizer = PromptOptimizer()
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from storage."""
        templates_file = self.storage_path / "templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    data = json.load(f)
                    
                    for template_data in data.get('templates', []):
                        template = PromptTemplate(
                            id=template_data['id'],
                            name=template_data['name'],
                            description=template_data['description'],
                            template=template_data['template'],
                            prompt_type=PromptType(template_data['prompt_type']),
                            version=template_data['version'],
                            created_at=datetime.fromisoformat(template_data['created_at']),
                            updated_at=datetime.fromisoformat(template_data['updated_at']),
                            variables=template_data.get('variables', []),
                            tags=template_data.get('tags', []),
                            metadata=template_data.get('metadata', {}),
                            is_active=template_data.get('is_active', True)
                        )
                        
                        # Load metrics
                        metrics_data = template_data.get('metrics', {})
                        template.metrics = PromptMetrics(
                            success_rate=metrics_data.get('success_rate', 0.0),
                            average_response_time=metrics_data.get('average_response_time', 0.0),
                            average_cost=metrics_data.get('average_cost', 0.0),
                            token_efficiency=metrics_data.get('token_efficiency', 0.0),
                            user_satisfaction=metrics_data.get('user_satisfaction', 0.0),
                            coherence_score=metrics_data.get('coherence_score', 0.0),
                            relevance_score=metrics_data.get('relevance_score', 0.0),
                            total_executions=metrics_data.get('total_executions', 0)
                        )
                        
                        self.templates[template.id] = template
                        
                        # Group by name for versioning
                        if template.name not in self.versions:
                            self.versions[template.name] = []
                        self.versions[template.name].append(template)
                        
            except Exception as e:
                logger.error(f"Failed to load templates: {e}")
    
    def _save_templates(self):
        """Save templates to storage."""
        templates_file = self.storage_path / "templates.json"
        try:
            data = {
                'templates': []
            }
            
            for template in self.templates.values():
                template_data = {
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'template': template.template,
                    'prompt_type': template.prompt_type.value,
                    'version': template.version,
                    'created_at': template.created_at.isoformat(),
                    'updated_at': template.updated_at.isoformat(),
                    'variables': template.variables,
                    'tags': template.tags,
                    'metadata': template.metadata,
                    'is_active': template.is_active,
                    'metrics': {
                        'success_rate': template.metrics.success_rate,
                        'average_response_time': template.metrics.average_response_time,
                        'average_cost': template.metrics.average_cost,
                        'token_efficiency': template.metrics.token_efficiency,
                        'user_satisfaction': template.metrics.user_satisfaction,
                        'coherence_score': template.metrics.coherence_score,
                        'relevance_score': template.metrics.relevance_score,
                        'total_executions': template.metrics.total_executions
                    }
                }
                data['templates'].append(template_data)
            
            with open(templates_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
    
    def create_template(
        self,
        name: str,
        template: str,
        prompt_type: PromptType,
        description: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """Create a new prompt template."""
        template_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract variables from template
        env = Environment()
        parsed = env.parse(template)
        variables = list(meta.find_undeclared_variables(parsed))
        
        # Determine version
        existing_versions = self.versions.get(name, [])
        if existing_versions:
            latest_version = max(existing_versions, key=lambda t: t.version)
            version_parts = latest_version.version.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            version = f"{major}.{minor + 1}"
        else:
            version = "1.0"
        
        prompt_template = PromptTemplate(
            id=template_id,
            name=name,
            description=description,
            template=template,
            prompt_type=prompt_type,
            version=version,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            variables=variables,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.templates[template_id] = prompt_template
        
        if name not in self.versions:
            self.versions[name] = []
        self.versions[name].append(prompt_template)
        
        self._save_templates()
        
        logger.info(f"Created prompt template {name} v{version}")
        return prompt_template
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_template_by_name(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """Get template by name and optional version."""
        templates = self.versions.get(name, [])
        
        if not templates:
            return None
        
        if version:
            for template in templates:
                if template.version == version and template.is_active:
                    return template
            return None
        
        # Return latest active version
        active_templates = [t for t in templates if t.is_active]
        if active_templates:
            return max(active_templates, key=lambda t: t.version)
        
        return None
    
    def list_templates(
        self,
        prompt_type: Optional[PromptType] = None,
        tags: Optional[List[str]] = None,
        active_only: bool = True
    ) -> List[PromptTemplate]:
        """List templates with optional filtering."""
        templates = list(self.templates.values())
        
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        if prompt_type:
            templates = [t for t in templates if t.prompt_type == prompt_type]
        
        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]
        
        return sorted(templates, key=lambda t: t.updated_at, reverse=True)
    
    async def render_template(
        self,
        template_id: str,
        context: Dict[str, Any],
        optimize: bool = False,
        optimization_strategy: Optional[OptimizationStrategy] = None
    ) -> Optional[str]:
        """Render template with context and optional optimization."""
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template {template_id} not found")
            return None
        
        try:
            rendered = template.render(context)
            
            if optimize and optimization_strategy:
                rendered = await self.optimizer.optimize_prompt(
                    rendered, optimization_strategy, context
                )
            
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render template {template_id}: {e}")
            return None
    
    async def optimize_template(
        self,
        template_id: str,
        strategy: OptimizationStrategy,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Optimize a template using specified strategy."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        return await self.optimizer.optimize_prompt(
            template.template, strategy, context or {}
        )
    
    def update_template_metrics(
        self,
        template_id: str,
        success: bool,
        response_time: float,
        cost: float,
        input_tokens: int,
        output_tokens: int,
        user_satisfaction: Optional[float] = None,
        coherence_score: Optional[float] = None,
        relevance_score: Optional[float] = None
    ) -> bool:
        """Update template performance metrics."""
        template = self.get_template(template_id)
        if not template:
            return False
        
        metrics = template.metrics
        total = metrics.total_executions
        
        # Update metrics using moving averages
        metrics.success_rate = (metrics.success_rate * total + (1 if success else 0)) / (total + 1)
        metrics.average_response_time = (metrics.average_response_time * total + response_time) / (total + 1)
        metrics.average_cost = (metrics.average_cost * total + cost) / (total + 1)
        
        if input_tokens > 0:
            token_efficiency = output_tokens / input_tokens
            metrics.token_efficiency = (metrics.token_efficiency * total + token_efficiency) / (total + 1)
        
        if user_satisfaction is not None:
            metrics.user_satisfaction = (metrics.user_satisfaction * total + user_satisfaction) / (total + 1)
        
        if coherence_score is not None:
            metrics.coherence_score = (metrics.coherence_score * total + coherence_score) / (total + 1)
        
        if relevance_score is not None:
            metrics.relevance_score = (metrics.relevance_score * total + relevance_score) / (total + 1)
        
        metrics.total_executions += 1
        template.updated_at = datetime.now()
        
        self._save_templates()
        return True
    
    def create_variant(
        self,
        template_id: str,
        new_template: str,
        description: str = "Template variant"
    ) -> Optional[PromptTemplate]:
        """Create a variant of an existing template."""
        original = self.get_template(template_id)
        if not original:
            return None
        
        return self.create_template(
            name=original.name,
            template=new_template,
            prompt_type=original.prompt_type,
            description=description,
            tags=original.tags + ["variant"],
            metadata={**original.metadata, "original_template_id": template_id}
        )
    
    def get_best_performing_template(
        self,
        name: str,
        metric: str = "success_rate"
    ) -> Optional[PromptTemplate]:
        """Get the best performing template version for a given name."""
        templates = self.versions.get(name, [])
        active_templates = [t for t in templates if t.is_active and t.metrics.total_executions > 0]
        
        if not active_templates:
            return None
        
        if metric == "success_rate":
            return max(active_templates, key=lambda t: t.metrics.success_rate)
        elif metric == "response_time":
            return min(active_templates, key=lambda t: t.metrics.average_response_time)
        elif metric == "cost":
            return min(active_templates, key=lambda t: t.metrics.average_cost)
        elif metric == "token_efficiency":
            return max(active_templates, key=lambda t: t.metrics.token_efficiency)
        elif metric == "user_satisfaction":
            return max(active_templates, key=lambda t: t.metrics.user_satisfaction)
        else:
            return max(active_templates, key=lambda t: t.metrics.success_rate)
    
    def get_template_analytics(self, name: str) -> Dict[str, Any]:
        """Get analytics for all versions of a template."""
        templates = self.versions.get(name, [])
        active_templates = [t for t in templates if t.is_active]
        
        if not active_templates:
            return {}
        
        analytics = {
            'name': name,
            'total_versions': len(templates),
            'active_versions': len(active_templates),
            'versions': []
        }
        
        for template in active_templates:
            version_data = {
                'id': template.id,
                'version': template.version,
                'created_at': template.created_at.isoformat(),
                'metrics': {
                    'success_rate': template.metrics.success_rate,
                    'average_response_time': template.metrics.average_response_time,
                    'average_cost': template.metrics.average_cost,
                    'token_efficiency': template.metrics.token_efficiency,
                    'user_satisfaction': template.metrics.user_satisfaction,
                    'coherence_score': template.metrics.coherence_score,
                    'relevance_score': template.metrics.relevance_score,
                    'total_executions': template.metrics.total_executions
                }
            }
            analytics['versions'].append(version_data)
        
        # Calculate aggregate statistics
        if active_templates:
            total_executions = sum(t.metrics.total_executions for t in active_templates)
            if total_executions > 0:
                analytics['aggregate'] = {
                    'weighted_success_rate': sum(
                        t.metrics.success_rate * t.metrics.total_executions 
                        for t in active_templates
                    ) / total_executions,
                    'weighted_average_cost': sum(
                        t.metrics.average_cost * t.metrics.total_executions 
                        for t in active_templates
                    ) / total_executions,
                    'total_executions': total_executions
                }
        
        return analytics
    
    def archive_template(self, template_id: str) -> bool:
        """Archive a template (mark as inactive)."""
        template = self.get_template(template_id)
        if template:
            template.is_active = False
            template.updated_at = datetime.now()
            self._save_templates()
            logger.info(f"Archived template {template_id}")
            return True
        return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template permanently."""
        if template_id in self.templates:
            template = self.templates[template_id]
            
            # Remove from templates
            del self.templates[template_id]
            
            # Remove from versions
            if template.name in self.versions:
                self.versions[template.name] = [
                    t for t in self.versions[template.name]
                    if t.id != template_id
                ]
                
                # Clean up empty version lists
                if not self.versions[template.name]:
                    del self.versions[template.name]
            
            self._save_templates()
            logger.info(f"Deleted template {template_id}")
            return True
        return False