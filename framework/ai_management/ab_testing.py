"""A/B Testing Framework for AI Models.

This module provides comprehensive A/B testing capabilities for comparing
AI model performance, including:
- Statistical significance testing
- Traffic splitting and routing
- Performance metric collection
- Automated experiment analysis
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field
from scipy import stats

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """A/B test experiment status."""
    
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TestMetric(str, Enum):
    """Available test metrics."""
    
    RESPONSE_TIME = "response_time"
    COST_PER_REQUEST = "cost_per_request"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"
    ACCURACY = "accuracy"
    COHERENCE = "coherence"
    RELEVANCE = "relevance"
    CUSTOM = "custom"


@dataclass
class TestGroup:
    """A/B test group configuration."""
    
    name: str
    model_name: str
    model_version: str
    traffic_percentage: float
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class ExperimentResult:
    """Result of an experiment measurement."""
    
    group_name: str
    metric: TestMetric
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTestConfig(BaseModel):
    """A/B test configuration."""
    
    name: str
    description: str
    groups: List[TestGroup]
    primary_metric: TestMetric
    secondary_metrics: List[TestMetric] = Field(default_factory=list)
    minimum_sample_size: int = 100
    significance_level: float = 0.05
    power: float = 0.8
    duration_days: int = 7
    traffic_allocation: Dict[str, float] = Field(default_factory=dict)
    success_criteria: Dict[str, Any] = Field(default_factory=dict)


class ABTestManager:
    """Manages A/B testing experiments for AI models."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("ab_tests")
        self.storage_path.mkdir(exist_ok=True)
        self.experiments: Dict[str, ABTestConfig] = {}
        self.experiment_status: Dict[str, ExperimentStatus] = {}
        self.results: Dict[str, List[ExperimentResult]] = {}
        self._load_experiments()
    
    def _load_experiments(self) -> None:
        """Load experiments from storage."""
        experiments_file = self.storage_path / "experiments.json"
        if experiments_file.exists():
            try:
                with open(experiments_file, 'r') as f:
                    data = json.load(f)
                    
                    for exp_id, exp_data in data.get('experiments', {}).items():
                        groups = [
                            TestGroup(
                                name=g['name'],
                                model_name=g['model_name'],
                                model_version=g['model_version'],
                                traffic_percentage=g['traffic_percentage'],
                                config_overrides=g.get('config_overrides', {}),
                                tags=g.get('tags', [])
                            )
                            for g in exp_data['groups']
                        ]
                        
                        self.experiments[exp_id] = ABTestConfig(
                            name=exp_data['name'],
                            description=exp_data['description'],
                            groups=groups,
                            primary_metric=TestMetric(exp_data['primary_metric']),
                            secondary_metrics=[TestMetric(m) for m in exp_data.get('secondary_metrics', [])],
                            minimum_sample_size=exp_data.get('minimum_sample_size', 100),
                            significance_level=exp_data.get('significance_level', 0.05),
                            power=exp_data.get('power', 0.8),
                            duration_days=exp_data.get('duration_days', 7),
                            traffic_allocation=exp_data.get('traffic_allocation', {}),
                            success_criteria=exp_data.get('success_criteria', {})
                        )
                    
                    self.experiment_status = {
                        exp_id: ExperimentStatus(status)
                        for exp_id, status in data.get('status', {}).items()
                    }
                    
                    # Load results
                    for exp_id, results_data in data.get('results', {}).items():
                        self.results[exp_id] = [
                            ExperimentResult(
                                group_name=r['group_name'],
                                metric=TestMetric(r['metric']),
                                value=r['value'],
                                timestamp=datetime.fromisoformat(r['timestamp']),
                                metadata=r.get('metadata', {})
                            )
                            for r in results_data
                        ]
                        
            except Exception as e:
                logger.error(f"Failed to load experiments: {e}")
    
    def _save_experiments(self) -> None:
        """Save experiments to storage."""
        experiments_file = self.storage_path / "experiments.json"
        try:
            data = {
                'experiments': {},
                'status': {exp_id: status.value for exp_id, status in self.experiment_status.items()},
                'results': {}
            }
            
            for exp_id, experiment in self.experiments.items():
                data['experiments'][exp_id] = {
                    'name': experiment.name,
                    'description': experiment.description,
                    'groups': [
                        {
                            'name': g.name,
                            'model_name': g.model_name,
                            'model_version': g.model_version,
                            'traffic_percentage': g.traffic_percentage,
                            'config_overrides': g.config_overrides,
                            'tags': g.tags
                        }
                        for g in experiment.groups
                    ],
                    'primary_metric': experiment.primary_metric.value,
                    'secondary_metrics': [m.value for m in experiment.secondary_metrics],
                    'minimum_sample_size': experiment.minimum_sample_size,
                    'significance_level': experiment.significance_level,
                    'power': experiment.power,
                    'duration_days': experiment.duration_days,
                    'traffic_allocation': experiment.traffic_allocation,
                    'success_criteria': experiment.success_criteria
                }
            
            for exp_id, results in self.results.items():
                data['results'][exp_id] = [
                    {
                        'group_name': r.group_name,
                        'metric': r.metric.value,
                        'value': r.value,
                        'timestamp': r.timestamp.isoformat(),
                        'metadata': r.metadata
                    }
                    for r in results
                ]
            
            with open(experiments_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save experiments: {e}")
    
    def create_experiment(
        self,
        name: str,
        description: str,
        groups: List[TestGroup],
        primary_metric: TestMetric,
        **kwargs
    ) -> str:
        """Create a new A/B test experiment."""
        experiment_id = str(uuid4())
        
        # Validate traffic allocation
        total_traffic = sum(g.traffic_percentage for g in groups)
        if abs(total_traffic - 100.0) > 0.1:
            raise ValueError(f"Traffic allocation must sum to 100%, got {total_traffic}%")
        
        # Create traffic allocation map
        traffic_allocation = {g.name: g.traffic_percentage for g in groups}
        
        experiment = ABTestConfig(
            name=name,
            description=description,
            groups=groups,
            primary_metric=primary_metric,
            traffic_allocation=traffic_allocation,
            **kwargs
        )
        
        self.experiments[experiment_id] = experiment
        self.experiment_status[experiment_id] = ExperimentStatus.DRAFT
        self.results[experiment_id] = []
        
        self._save_experiments()
        
        logger.info(f"Created experiment '{name}' with ID {experiment_id}")
        return experiment_id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment."""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        if self.experiment_status[experiment_id] != ExperimentStatus.DRAFT:
            logger.error(f"Experiment {experiment_id} is not in draft status")
            return False
        
        self.experiment_status[experiment_id] = ExperimentStatus.RUNNING
        self._save_experiments()
        
        logger.info(f"Started experiment {experiment_id}")
        return True
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment."""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        if self.experiment_status[experiment_id] != ExperimentStatus.RUNNING:
            logger.error(f"Experiment {experiment_id} is not running")
            return False
        
        self.experiment_status[experiment_id] = ExperimentStatus.COMPLETED
        self._save_experiments()
        
        logger.info(f"Stopped experiment {experiment_id}")
        return True
    
    def assign_to_group(
        self,
        experiment_id: str,
        user_id: Optional[str] = None
    ) -> Optional[TestGroup]:
        """Assign a request to an experiment group."""
        if experiment_id not in self.experiments:
            return None
        
        if self.experiment_status[experiment_id] != ExperimentStatus.RUNNING:
            return None
        
        experiment = self.experiments[experiment_id]
        
        # Use deterministic assignment if user_id provided
        if user_id:
            hash_val = hash(f"{experiment_id}:{user_id}") % 100
        else:
            hash_val = random.randint(0, 99)
        
        # Assign based on traffic allocation
        cumulative = 0
        for group in experiment.groups:
            cumulative += group.traffic_percentage
            if hash_val < cumulative:
                return group
        
        # Fallback to last group
        return experiment.groups[-1] if experiment.groups else None
    
    def record_result(
        self,
        experiment_id: str,
        group_name: str,
        metric: TestMetric,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an experiment result."""
        if experiment_id not in self.experiments:
            logger.error(f"Experiment {experiment_id} not found")
            return False
        
        result = ExperimentResult(
            group_name=group_name,
            metric=metric,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.results[experiment_id].append(result)
        self._save_experiments()
        
        return True
    
    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment statistics."""
        if experiment_id not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_id]
        results = self.results[experiment_id]
        
        stats_data = {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'status': self.experiment_status[experiment_id].value,
            'groups': {},
            'total_samples': len(results),
            'analysis': {}
        }
        
        # Group results by group and metric
        grouped_results = {}
        for result in results:
            key = (result.group_name, result.metric)
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].append(result.value)
        
        # Calculate stats for each group
        for group in experiment.groups:
            group_stats = {
                'name': group.name,
                'model': f"{group.model_name}:{group.model_version}",
                'traffic_percentage': group.traffic_percentage,
                'metrics': {}
            }
            
            for metric in [experiment.primary_metric] + experiment.secondary_metrics:
                key = (group.name, metric)
                values = grouped_results.get(key, [])
                
                if values:
                    group_stats['metrics'][metric.value] = {
                        'count': len(values),
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'median': np.median(values)
                    }
                else:
                    group_stats['metrics'][metric.value] = {
                        'count': 0,
                        'mean': 0,
                        'std': 0,
                        'min': 0,
                        'max': 0,
                        'median': 0
                    }
            
            stats_data['groups'][group.name] = group_stats
        
        # Statistical analysis
        if len(experiment.groups) == 2:
            stats_data['analysis'] = self._perform_statistical_analysis(
                experiment, grouped_results
            )
        
        return stats_data
    
    def _perform_statistical_analysis(
        self,
        experiment: ABTestConfig,
        grouped_results: Dict[tuple, List[float]]
    ) -> Dict[str, Any]:
        """Perform statistical analysis for two-group experiments."""
        analysis = {}
        
        if len(experiment.groups) != 2:
            return analysis
        
        group_a, group_b = experiment.groups
        
        for metric in [experiment.primary_metric] + experiment.secondary_metrics:
            key_a = (group_a.name, metric)
            key_b = (group_b.name, metric)
            
            values_a = grouped_results.get(key_a, [])
            values_b = grouped_results.get(key_b, [])
            
            if len(values_a) < experiment.minimum_sample_size or len(values_b) < experiment.minimum_sample_size:
                analysis[metric.value] = {
                    'test': 'insufficient_data',
                    'samples_needed': experiment.minimum_sample_size - min(len(values_a), len(values_b)),
                    'current_samples': {'group_a': len(values_a), 'group_b': len(values_b)}
                }
                continue
            
            # Perform t-test
            try:
                t_stat, p_value = stats.ttest_ind(values_a, values_b)
                
                # Calculate effect size (Cohen's d)
                pooled_std = np.sqrt(((len(values_a) - 1) * np.var(values_a, ddof=1) + 
                                    (len(values_b) - 1) * np.var(values_b, ddof=1)) / 
                                   (len(values_a) + len(values_b) - 2))
                effect_size = (np.mean(values_a) - np.mean(values_b)) / pooled_std if pooled_std > 0 else 0
                
                # Determine significance
                is_significant = p_value < experiment.significance_level
                
                # Calculate confidence interval for difference in means
                diff_mean = np.mean(values_a) - np.mean(values_b)
                se_diff = pooled_std * np.sqrt(1/len(values_a) + 1/len(values_b))
                t_critical = stats.t.ppf(1 - experiment.significance_level/2, len(values_a) + len(values_b) - 2)
                ci_lower = diff_mean - t_critical * se_diff
                ci_upper = diff_mean + t_critical * se_diff
                
                analysis[metric.value] = {
                    'test': 't_test',
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'is_significant': is_significant,
                    'effect_size': float(effect_size),
                    'difference': {
                        'mean': float(diff_mean),
                        'confidence_interval': [float(ci_lower), float(ci_upper)],
                        'relative_improvement': float((diff_mean / np.mean(values_b)) * 100) if np.mean(values_b) != 0 else 0
                    }
                }
                
            except Exception as e:
                logger.error(f"Statistical analysis failed for metric {metric.value}: {e}")
                analysis[metric.value] = {
                    'test': 'failed',
                    'error': str(e)
                }
        
        return analysis
    
    def get_winning_variant(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Determine the winning variant based on primary metric."""
        stats = self.get_experiment_stats(experiment_id)
        
        if not stats or 'analysis' not in stats:
            return None
        
        experiment = self.experiments[experiment_id]
        primary_metric = experiment.primary_metric.value
        
        if primary_metric not in stats['analysis']:
            return None
        
        analysis = stats['analysis'][primary_metric]
        
        if analysis.get('test') != 't_test' or not analysis.get('is_significant'):
            return {
                'winner': None,
                'confidence': 'low',
                'reason': 'No statistically significant difference found'
            }
        
        # Determine winner based on metric type (higher is better for most metrics)
        improvement = analysis['difference']['relative_improvement']
        
        if abs(improvement) < 1.0:  # Less than 1% improvement
            return {
                'winner': None,
                'confidence': 'low',
                'reason': f'Improvement too small: {improvement:.2f}%'
            }
        
        group_a, group_b = experiment.groups
        winner = group_a.name if improvement > 0 else group_b.name
        
        return {
            'winner': winner,
            'confidence': 'high' if analysis['p_value'] < 0.01 else 'medium',
            'improvement': f"{abs(improvement):.2f}%",
            'p_value': analysis['p_value'],
            'effect_size': analysis['effect_size']
        }
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all experiments with optional status filter."""
        experiments = []
        
        for exp_id, experiment in self.experiments.items():
            exp_status = self.experiment_status[exp_id]
            
            if status and exp_status != status:
                continue
            
            experiments.append({
                'id': exp_id,
                'name': experiment.name,
                'status': exp_status.value,
                'groups': len(experiment.groups),
                'primary_metric': experiment.primary_metric.value,
                'results_count': len(self.results.get(exp_id, []))
            })
        
        return experiments
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment and its results."""
        if experiment_id not in self.experiments:
            return False
        
        del self.experiments[experiment_id]
        del self.experiment_status[experiment_id]
        if experiment_id in self.results:
            del self.results[experiment_id]
        
        self._save_experiments()
        logger.info(f"Deleted experiment {experiment_id}")
        return True