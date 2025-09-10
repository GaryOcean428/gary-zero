"""Cost optimization and analytics system for AI models.

This module provides comprehensive cost management capabilities including:
- Real-time cost tracking and budgeting
- Cost-efficient model selection
- Usage analytics and reporting
- Cost optimization recommendations
- Budget alerts and controls
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BudgetPeriod(str, Enum):
    """Budget period types."""
    
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AlertType(str, Enum):
    """Alert types for budget monitoring."""
    
    THRESHOLD_WARNING = "threshold_warning"
    THRESHOLD_CRITICAL = "threshold_critical"
    BUDGET_EXCEEDED = "budget_exceeded"
    ANOMALY_DETECTED = "anomaly_detected"
    COST_SPIKE = "cost_spike"


class OptimizationRecommendationType(str, Enum):
    """Types of cost optimization recommendations."""
    
    MODEL_SWITCH = "model_switch"
    CACHING_IMPROVEMENT = "caching_improvement"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    BATCH_PROCESSING = "batch_processing"
    USAGE_PATTERN_OPTIMIZATION = "usage_pattern_optimization"


@dataclass
class CostEntry:
    """Individual cost entry."""
    
    timestamp: datetime
    model_name: str
    model_version: str
    provider: str
    input_tokens: int
    output_tokens: int
    cost_input: float
    cost_output: float
    total_cost: float
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostBudget:
    """Budget configuration and tracking."""
    
    name: str
    limit: float
    period: BudgetPeriod
    start_date: datetime
    end_date: Optional[datetime] = None
    spent: float = 0.0
    remaining: float = 0.0
    warning_threshold: float = 0.8  # 80%
    critical_threshold: float = 0.95  # 95%
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.remaining = self.limit - self.spent
    
    @property
    def usage_percentage(self) -> float:
        """Get budget usage percentage."""
        return (self.spent / self.limit) * 100 if self.limit > 0 else 0
    
    @property
    def is_warning(self) -> bool:
        """Check if budget is at warning threshold."""
        return self.usage_percentage >= (self.warning_threshold * 100)
    
    @property
    def is_critical(self) -> bool:
        """Check if budget is at critical threshold."""
        return self.usage_percentage >= (self.critical_threshold * 100)
    
    @property
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.spent >= self.limit


@dataclass
class UsageMetrics:
    """Usage metrics for analytics."""
    
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_cost_per_request: float = 0.0
    average_tokens_per_request: float = 0.0
    cost_per_token: float = 0.0
    peak_usage_hour: Optional[int] = None
    most_expensive_model: Optional[str] = None
    most_used_model: Optional[str] = None


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    
    type: OptimizationRecommendationType
    title: str
    description: str
    estimated_savings: float
    estimated_savings_percent: float
    confidence: float  # 0-1
    implementation_effort: str  # "low", "medium", "high"
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class CostOptimizer:
    """Manages cost optimization and analytics."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("cost_data")
        self.storage_path.mkdir(exist_ok=True)
        
        self.cost_entries: List[CostEntry] = []
        self.budgets: Dict[str, CostBudget] = {}
        self.alerts: List[Dict[str, Any]] = []
        
        self._load_data()
    
    def _load_data(self):
        """Load cost data from storage."""
        # Load cost entries
        costs_file = self.storage_path / "cost_entries.json"
        if costs_file.exists():
            try:
                with open(costs_file, 'r') as f:
                    data = json.load(f)
                    for entry_data in data:
                        entry = CostEntry(
                            timestamp=datetime.fromisoformat(entry_data['timestamp']),
                            model_name=entry_data['model_name'],
                            model_version=entry_data['model_version'],
                            provider=entry_data['provider'],
                            input_tokens=entry_data['input_tokens'],
                            output_tokens=entry_data['output_tokens'],
                            cost_input=entry_data['cost_input'],
                            cost_output=entry_data['cost_output'],
                            total_cost=entry_data['total_cost'],
                            request_id=entry_data['request_id'],
                            user_id=entry_data.get('user_id'),
                            session_id=entry_data.get('session_id'),
                            metadata=entry_data.get('metadata', {})
                        )
                        self.cost_entries.append(entry)
            except Exception as e:
                logger.error(f"Failed to load cost entries: {e}")
        
        # Load budgets
        budgets_file = self.storage_path / "budgets.json"
        if budgets_file.exists():
            try:
                with open(budgets_file, 'r') as f:
                    data = json.load(f)
                    for budget_id, budget_data in data.items():
                        budget = CostBudget(
                            name=budget_data['name'],
                            limit=budget_data['limit'],
                            period=BudgetPeriod(budget_data['period']),
                            start_date=datetime.fromisoformat(budget_data['start_date']),
                            end_date=datetime.fromisoformat(budget_data['end_date']) if budget_data.get('end_date') else None,
                            spent=budget_data.get('spent', 0.0),
                            warning_threshold=budget_data.get('warning_threshold', 0.8),
                            critical_threshold=budget_data.get('critical_threshold', 0.95),
                            is_active=budget_data.get('is_active', True),
                            metadata=budget_data.get('metadata', {})
                        )
                        self.budgets[budget_id] = budget
            except Exception as e:
                logger.error(f"Failed to load budgets: {e}")
        
        # Load alerts
        alerts_file = self.storage_path / "alerts.json"
        if alerts_file.exists():
            try:
                with open(alerts_file, 'r') as f:
                    self.alerts = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load alerts: {e}")
    
    def _save_data(self):
        """Save cost data to storage."""
        # Save cost entries (keep only recent ones to manage size)
        costs_file = self.storage_path / "cost_entries.json"
        try:
            # Keep only last 30 days of entries
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_entries = [
                e for e in self.cost_entries 
                if e.timestamp >= cutoff_date
            ]
            
            data = []
            for entry in recent_entries:
                data.append({
                    'timestamp': entry.timestamp.isoformat(),
                    'model_name': entry.model_name,
                    'model_version': entry.model_version,
                    'provider': entry.provider,
                    'input_tokens': entry.input_tokens,
                    'output_tokens': entry.output_tokens,
                    'cost_input': entry.cost_input,
                    'cost_output': entry.cost_output,
                    'total_cost': entry.total_cost,
                    'request_id': entry.request_id,
                    'user_id': entry.user_id,
                    'session_id': entry.session_id,
                    'metadata': entry.metadata
                })
            
            with open(costs_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save cost entries: {e}")
        
        # Save budgets
        budgets_file = self.storage_path / "budgets.json"
        try:
            data = {}
            for budget_id, budget in self.budgets.items():
                data[budget_id] = {
                    'name': budget.name,
                    'limit': budget.limit,
                    'period': budget.period.value,
                    'start_date': budget.start_date.isoformat(),
                    'end_date': budget.end_date.isoformat() if budget.end_date else None,
                    'spent': budget.spent,
                    'warning_threshold': budget.warning_threshold,
                    'critical_threshold': budget.critical_threshold,
                    'is_active': budget.is_active,
                    'metadata': budget.metadata
                }
            
            with open(budgets_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save budgets: {e}")
        
        # Save alerts
        alerts_file = self.storage_path / "alerts.json"
        try:
            with open(alerts_file, 'w') as f:
                json.dump(self.alerts, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def record_cost(
        self,
        model_name: str,
        model_version: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost_input: float,
        cost_output: float,
        request_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a cost entry."""
        total_cost = cost_input + cost_output
        
        entry = CostEntry(
            timestamp=datetime.now(),
            model_name=model_name,
            model_version=model_version,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_input=cost_input,
            cost_output=cost_output,
            total_cost=total_cost,
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        self.cost_entries.append(entry)
        
        # Update budgets
        self._update_budgets(total_cost)
        
        # Check for alerts
        self._check_budget_alerts()
        
        # Periodically save data
        if len(self.cost_entries) % 100 == 0:
            self._save_data()
        
        return True
    
    def _update_budgets(self, cost: float):
        """Update budget spending."""
        for budget in self.budgets.values():
            if budget.is_active and self._is_budget_applicable(budget):
                budget.spent += cost
                budget.remaining = budget.limit - budget.spent
    
    def _is_budget_applicable(self, budget: CostBudget) -> bool:
        """Check if budget applies to current time period."""
        now = datetime.now()
        
        if budget.end_date and now > budget.end_date:
            return False
        
        # Check if we're in the current budget period
        if budget.period == BudgetPeriod.HOURLY:
            return now.hour == budget.start_date.hour
        elif budget.period == BudgetPeriod.DAILY:
            return now.date() == budget.start_date.date()
        elif budget.period == BudgetPeriod.WEEKLY:
            # Same week
            return now.isocalendar()[1] == budget.start_date.isocalendar()[1]
        elif budget.period == BudgetPeriod.MONTHLY:
            return now.month == budget.start_date.month and now.year == budget.start_date.year
        elif budget.period == BudgetPeriod.YEARLY:
            return now.year == budget.start_date.year
        
        return True
    
    def _check_budget_alerts(self):
        """Check budgets for alerts."""
        for budget_id, budget in self.budgets.items():
            if not budget.is_active:
                continue
            
            alert_data = {
                'budget_id': budget_id,
                'budget_name': budget.name,
                'timestamp': datetime.now().isoformat(),
                'usage_percentage': budget.usage_percentage,
                'spent': budget.spent,
                'limit': budget.limit
            }
            
            if budget.is_exceeded:
                alert_data.update({
                    'type': AlertType.BUDGET_EXCEEDED.value,
                    'message': f"Budget '{budget.name}' has been exceeded",
                    'severity': 'critical'
                })
                self.alerts.append(alert_data)
                
            elif budget.is_critical:
                alert_data.update({
                    'type': AlertType.THRESHOLD_CRITICAL.value,
                    'message': f"Budget '{budget.name}' is at critical threshold",
                    'severity': 'critical'
                })
                self.alerts.append(alert_data)
                
            elif budget.is_warning:
                alert_data.update({
                    'type': AlertType.THRESHOLD_WARNING.value,
                    'message': f"Budget '{budget.name}' is at warning threshold",
                    'severity': 'warning'
                })
                self.alerts.append(alert_data)
    
    def create_budget(
        self,
        name: str,
        limit: float,
        period: BudgetPeriod,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95
    ) -> str:
        """Create a new budget."""
        budget_id = f"budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        budget = CostBudget(
            name=name,
            limit=limit,
            period=period,
            start_date=start_date or datetime.now(),
            end_date=end_date,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold
        )
        
        self.budgets[budget_id] = budget
        self._save_data()
        
        logger.info(f"Created budget '{name}' with limit ${limit}")
        return budget_id
    
    def get_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_name: Optional[str] = None,
        provider: Optional[str] = None
    ) -> UsageMetrics:
        """Get usage metrics for specified period and filters."""
        # Filter entries
        entries = self.cost_entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        if model_name:
            entries = [e for e in entries if e.model_name == model_name]
        
        if provider:
            entries = [e for e in entries if e.provider == provider]
        
        if not entries:
            return UsageMetrics()
        
        # Calculate metrics
        total_requests = len(entries)
        total_tokens = sum(e.input_tokens + e.output_tokens for e in entries)
        total_cost = sum(e.total_cost for e in entries)
        
        metrics = UsageMetrics(
            total_requests=total_requests,
            total_tokens=total_tokens,
            total_cost=total_cost,
            average_cost_per_request=total_cost / total_requests if total_requests > 0 else 0,
            average_tokens_per_request=total_tokens / total_requests if total_requests > 0 else 0,
            cost_per_token=total_cost / total_tokens if total_tokens > 0 else 0
        )
        
        # Find peak usage hour
        hour_costs = {}
        for entry in entries:
            hour = entry.timestamp.hour
            hour_costs[hour] = hour_costs.get(hour, 0) + entry.total_cost
        
        if hour_costs:
            metrics.peak_usage_hour = max(hour_costs, key=hour_costs.get)
        
        # Find most expensive model
        model_costs = {}
        for entry in entries:
            model_key = f"{entry.model_name}:{entry.model_version}"
            model_costs[model_key] = model_costs.get(model_key, 0) + entry.total_cost
        
        if model_costs:
            metrics.most_expensive_model = max(model_costs, key=model_costs.get)
        
        # Find most used model
        model_usage = {}
        for entry in entries:
            model_key = f"{entry.model_name}:{entry.model_version}"
            model_usage[model_key] = model_usage.get(model_key, 0) + 1
        
        if model_usage:
            metrics.most_used_model = max(model_usage, key=model_usage.get)
        
        return metrics
    
    def get_cost_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "model"  # "model", "provider", "user", "hour", "day"
    ) -> Dict[str, float]:
        """Get cost breakdown by specified grouping."""
        entries = self.cost_entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        breakdown = {}
        
        for entry in entries:
            if group_by == "model":
                key = f"{entry.model_name}:{entry.model_version}"
            elif group_by == "provider":
                key = entry.provider
            elif group_by == "user":
                key = entry.user_id or "unknown"
            elif group_by == "hour":
                key = entry.timestamp.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = entry.timestamp.strftime("%Y-%m-%d")
            else:
                key = "total"
            
            breakdown[key] = breakdown.get(key, 0) + entry.total_cost
        
        return breakdown
    
    def generate_optimization_recommendations(
        self,
        days_to_analyze: int = 7
    ) -> List[OptimizationRecommendation]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Analyze recent usage
        cutoff_date = datetime.now() - timedelta(days=days_to_analyze)
        recent_entries = [e for e in self.cost_entries if e.timestamp >= cutoff_date]
        
        if not recent_entries:
            return recommendations
        
        # Recommendation 1: Model switching
        model_recommendations = self._analyze_model_efficiency(recent_entries)
        recommendations.extend(model_recommendations)
        
        # Recommendation 2: Caching improvements
        caching_recommendations = self._analyze_caching_opportunities(recent_entries)
        recommendations.extend(caching_recommendations)
        
        # Recommendation 3: Prompt optimization
        prompt_recommendations = self._analyze_prompt_efficiency(recent_entries)
        recommendations.extend(prompt_recommendations)
        
        # Recommendation 4: Usage pattern optimization
        pattern_recommendations = self._analyze_usage_patterns(recent_entries)
        recommendations.extend(pattern_recommendations)
        
        return sorted(recommendations, key=lambda r: r.estimated_savings, reverse=True)
    
    def _analyze_model_efficiency(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Analyze model efficiency and suggest alternatives."""
        recommendations = []
        
        # Group by model and calculate efficiency metrics
        model_stats = {}
        for entry in entries:
            model_key = f"{entry.model_name}:{entry.model_version}"
            if model_key not in model_stats:
                model_stats[model_key] = {
                    'total_cost': 0,
                    'total_tokens': 0,
                    'requests': 0,
                    'provider': entry.provider
                }
            
            stats = model_stats[model_key]
            stats['total_cost'] += entry.total_cost
            stats['total_tokens'] += entry.input_tokens + entry.output_tokens
            stats['requests'] += 1
        
        # Find expensive models with potential alternatives
        for model_key, stats in model_stats.items():
            if stats['total_cost'] > 10:  # Only for models with significant cost
                cost_per_token = stats['total_cost'] / stats['total_tokens'] if stats['total_tokens'] > 0 else 0
                
                # Suggest switching to more cost-effective models
                if cost_per_token > 0.001:  # Arbitrary threshold
                    estimated_savings = stats['total_cost'] * 0.3  # Assume 30% savings
                    
                    recommendation = OptimizationRecommendation(
                        type=OptimizationRecommendationType.MODEL_SWITCH,
                        title=f"Switch from {model_key} to more cost-effective alternative",
                        description=f"Consider switching to a more cost-effective model. Current cost per token: ${cost_per_token:.6f}",
                        estimated_savings=estimated_savings,
                        estimated_savings_percent=30.0,
                        confidence=0.7,
                        implementation_effort="medium",
                        details={
                            'current_model': model_key,
                            'current_cost_per_token': cost_per_token,
                            'total_cost': stats['total_cost'],
                            'requests': stats['requests']
                        }
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_caching_opportunities(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Analyze caching opportunities."""
        recommendations = []
        
        # Look for repeated patterns that could benefit from caching
        prompt_hashes = {}
        for entry in entries:
            # Simple hash based on model and approximate prompt characteristics
            prompt_hash = f"{entry.model_name}_{entry.input_tokens // 100}"  # Group by 100-token buckets
            
            if prompt_hash not in prompt_hashes:
                prompt_hashes[prompt_hash] = []
            prompt_hashes[prompt_hash].append(entry)
        
        # Find patterns with multiple similar requests
        for prompt_hash, hash_entries in prompt_hashes.items():
            if len(hash_entries) >= 3:  # At least 3 similar requests
                total_cost = sum(e.total_cost for e in hash_entries)
                if total_cost > 1:  # Significant cost
                    estimated_savings = total_cost * 0.5  # Assume 50% cache hit rate
                    
                    recommendation = OptimizationRecommendation(
                        type=OptimizationRecommendationType.CACHING_IMPROVEMENT,
                        title=f"Implement caching for repeated patterns",
                        description=f"Found {len(hash_entries)} similar requests that could benefit from caching",
                        estimated_savings=estimated_savings,
                        estimated_savings_percent=50.0,
                        confidence=0.8,
                        implementation_effort="low",
                        details={
                            'pattern': prompt_hash,
                            'occurrences': len(hash_entries),
                            'total_cost': total_cost
                        }
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_prompt_efficiency(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Analyze prompt efficiency."""
        recommendations = []
        
        # Find prompts with high input token usage
        high_token_entries = [e for e in entries if e.input_tokens > 1000]
        
        if high_token_entries:
            total_cost = sum(e.total_cost for e in high_token_entries)
            if total_cost > 5:  # Significant cost
                estimated_savings = total_cost * 0.2  # Assume 20% reduction
                
                recommendation = OptimizationRecommendation(
                    type=OptimizationRecommendationType.PROMPT_OPTIMIZATION,
                    title="Optimize long prompts to reduce token usage",
                    description=f"Found {len(high_token_entries)} requests with >1000 input tokens",
                    estimated_savings=estimated_savings,
                    estimated_savings_percent=20.0,
                    confidence=0.6,
                    implementation_effort="medium",
                    details={
                        'high_token_requests': len(high_token_entries),
                        'total_cost': total_cost,
                        'average_tokens': sum(e.input_tokens for e in high_token_entries) / len(high_token_entries)
                    }
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _analyze_usage_patterns(
        self,
        entries: List[CostEntry]
    ) -> List[OptimizationRecommendation]:
        """Analyze usage patterns for optimization opportunities."""
        recommendations = []
        
        # Analyze hourly usage patterns
        hourly_costs = {}
        for entry in entries:
            hour = entry.timestamp.hour
            hourly_costs[hour] = hourly_costs.get(hour, 0) + entry.total_cost
        
        if hourly_costs:
            peak_hours = sorted(hourly_costs.items(), key=lambda x: x[1], reverse=True)[:3]
            off_peak_hours = sorted(hourly_costs.items(), key=lambda x: x[1])[:3]
            
            peak_cost = sum(cost for _, cost in peak_hours)
            total_cost = sum(hourly_costs.values())
            
            if peak_cost / total_cost > 0.5:  # More than 50% of cost in peak hours
                estimated_savings = peak_cost * 0.15  # Assume 15% savings from load shifting
                
                recommendation = OptimizationRecommendation(
                    type=OptimizationRecommendationType.USAGE_PATTERN_OPTIMIZATION,
                    title="Optimize usage patterns to reduce peak-hour costs",
                    description="Consider shifting non-urgent requests to off-peak hours",
                    estimated_savings=estimated_savings,
                    estimated_savings_percent=15.0,
                    confidence=0.5,
                    implementation_effort="high",
                    details={
                        'peak_hours': [hour for hour, _ in peak_hours],
                        'off_peak_hours': [hour for hour, _ in off_peak_hours],
                        'peak_cost_percentage': (peak_cost / total_cost) * 100
                    }
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def get_budget_status(self) -> List[Dict[str, Any]]:
        """Get status of all budgets."""
        status_list = []
        
        for budget_id, budget in self.budgets.items():
            status = {
                'id': budget_id,
                'name': budget.name,
                'limit': budget.limit,
                'spent': budget.spent,
                'remaining': budget.remaining,
                'usage_percentage': budget.usage_percentage,
                'period': budget.period.value,
                'is_active': budget.is_active,
                'is_warning': budget.is_warning,
                'is_critical': budget.is_critical,
                'is_exceeded': budget.is_exceeded,
                'start_date': budget.start_date.isoformat(),
                'end_date': budget.end_date.isoformat() if budget.end_date else None
            }
            status_list.append(status)
        
        return status_list
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return sorted(self.alerts, key=lambda a: a['timestamp'], reverse=True)[:limit]
    
    def export_cost_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> Union[Dict[str, Any], str]:
        """Export cost report."""
        metrics = self.get_usage_metrics(start_date, end_date)
        cost_breakdown = self.get_cost_breakdown(start_date, end_date, "model")
        budget_status = self.get_budget_status()
        recommendations = self.generate_optimization_recommendations()
        
        report = {
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_cost': metrics.total_cost,
                'total_requests': metrics.total_requests,
                'total_tokens': metrics.total_tokens,
                'average_cost_per_request': metrics.average_cost_per_request,
                'cost_per_token': metrics.cost_per_token
            },
            'breakdown': cost_breakdown,
            'budgets': budget_status,
            'recommendations': [
                {
                    'type': r.type.value,
                    'title': r.title,
                    'description': r.description,
                    'estimated_savings': r.estimated_savings,
                    'confidence': r.confidence
                }
                for r in recommendations[:5]  # Top 5 recommendations
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        if format == "json":
            return report
        else:
            # Simple text format
            lines = [
                "COST REPORT",
                "=" * 50,
                f"Total Cost: ${metrics.total_cost:.4f}",
                f"Total Requests: {metrics.total_requests}",
                f"Average Cost per Request: ${metrics.average_cost_per_request:.6f}",
                "",
                "TOP MODELS BY COST:",
                "-" * 20
            ]
            
            for model, cost in sorted(cost_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"{model}: ${cost:.4f}")
            
            return "\n".join(lines)