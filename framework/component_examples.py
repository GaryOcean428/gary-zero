"""
Component Examples and Integration Patterns

This module provides concrete examples of how to implement and use
the modular component system in various scenarios, demonstrating
best practices and integration patterns.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from .modular_component_system import (
    BaseComponent, ComponentMetadata, ComponentConfig, ComponentType,
    ComponentState, ComponentManager, create_component_manager
)

logger = logging.getLogger(__name__)


class AnalyticsPanel(BaseComponent):
    """
    Advanced analytics panel component that demonstrates:
    - Real-time data processing
    - Inter-component communication
    - Advanced configuration validation
    - Performance optimization
    """
    
    def __init__(self, metadata, config, event_bus, analytics):
        super().__init__(metadata, config, event_bus, analytics)
        self.data_processors = {}
        self.active_queries = {}
        self.cache_hit_rate = 0.0
        
    async def _initialize(self) -> None:
        """Initialize analytics panel with data processors"""
        # Initialize data processing pipeline
        self.data_processors = {
            'real_time': self._process_realtime_data,
            'batch': self._process_batch_data,
            'predictive': self._process_predictive_data
        }
        
        # Subscribe to data events
        self.event_bus.subscribe('data.stream', self._handle_data_stream)
        self.event_bus.subscribe('query.request', self._handle_query_request)
        
        # Initialize cache
        self.cache = {}
        self.cache_timestamps = {}
        
        logger.info("Analytics panel initialized with data processors")
    
    async def _start(self) -> None:
        """Start the analytics panel"""
        # Start background tasks
        asyncio.create_task(self._cache_cleanup_loop())
        asyncio.create_task(self._performance_monitor_loop())
        
        # Emit ready event
        await self.event_bus.emit(
            'analytics.ready',
            {'instance_id': self.config.instance_id, 'capabilities': list(self.data_processors.keys())},
            self.config.instance_id
        )
    
    async def _stop(self) -> None:
        """Stop analytics processing"""
        # Cancel active queries
        for query_id in list(self.active_queries.keys()):
            await self._cancel_query(query_id)
        
        # Clear cache
        self.cache.clear()
        self.cache_timestamps.clear()
    
    async def _destroy(self) -> None:
        """Clean up analytics panel"""
        self.event_bus.unsubscribe('data.stream', self._handle_data_stream)
        self.event_bus.unsubscribe('query.request', self._handle_query_request)
    
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate analytics panel settings"""
        validated = {}
        
        # Cache settings
        if 'cache_ttl' in settings:
            ttl = settings['cache_ttl']
            if isinstance(ttl, (int, float)) and ttl > 0:
                validated['cache_ttl'] = max(60, int(ttl))  # Minimum 1 minute
        
        # Query timeout
        if 'query_timeout' in settings:
            timeout = settings['query_timeout']
            if isinstance(timeout, (int, float)) and timeout > 0:
                validated['query_timeout'] = max(5, int(timeout))  # Minimum 5 seconds
        
        # Max concurrent queries
        if 'max_concurrent_queries' in settings:
            max_queries = settings['max_concurrent_queries']
            if isinstance(max_queries, int) and max_queries > 0:
                validated['max_concurrent_queries'] = min(50, max(1, max_queries))
        
        # Data retention
        if 'data_retention_days' in settings:
            retention = settings['data_retention_days']
            if isinstance(retention, (int, float)) and retention > 0:
                validated['data_retention_days'] = max(1, int(retention))
        
        return validated
    
    def _on_config_changed(self, old_settings: Dict[str, Any], new_settings: Dict[str, Any]) -> None:
        """Handle configuration changes"""
        if old_settings.get('cache_ttl') != new_settings.get('cache_ttl'):
            # Clear existing cache if TTL changed
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("Cache cleared due to TTL change")
    
    def _get_custom_status(self) -> Dict[str, Any]:
        """Get analytics panel specific status"""
        return {
            'active_queries': len(self.active_queries),
            'cache_size': len(self.cache),
            'cache_hit_rate': self.cache_hit_rate,
            'data_processors': list(self.data_processors.keys()),
            'performance_metrics': self._get_performance_metrics()
        }
    
    async def _handle_data_stream(self, event: Dict) -> None:
        """Handle incoming data stream"""
        data = event.get('data', {})
        stream_type = data.get('type', 'unknown')
        
        # Track data ingestion
        self.analytics.track_user_interaction(
            self.config.instance_id,
            'data_ingestion',
            'system',
            {'stream_type': stream_type, 'data_size': len(str(data))}
        )
        
        # Process data based on type
        if stream_type in self.data_processors:
            await self.data_processors[stream_type](data)
    
    async def _handle_query_request(self, event: Dict) -> None:
        """Handle analytics query requests"""
        data = event.get('data', {})
        query_id = data.get('query_id')
        query_type = data.get('type', 'standard')
        
        if len(self.active_queries) >= self.config.settings.get('max_concurrent_queries', 10):
            await self.event_bus.emit(
                'query.rejected',
                {'query_id': query_id, 'reason': 'max_concurrent_queries_exceeded'},
                self.config.instance_id
            )
            return
        
        # Execute query
        self.active_queries[query_id] = {
            'start_time': time.time(),
            'type': query_type,
            'status': 'running'
        }
        
        try:
            result = await self._execute_query(data)
            
            await self.event_bus.emit(
                'query.completed',
                {'query_id': query_id, 'result': result},
                self.config.instance_id
            )
            
        except Exception as e:
            await self.event_bus.emit(
                'query.failed',
                {'query_id': query_id, 'error': str(e)},
                self.config.instance_id
            )
            
        finally:
            if query_id in self.active_queries:
                query_info = self.active_queries.pop(query_id)
                duration = time.time() - query_info['start_time']
                self.analytics.track_performance(
                    self.config.instance_id,
                    f"query_{query_type}",
                    duration
                )
    
    async def _execute_query(self, query_data: Dict) -> Dict[str, Any]:
        """Execute analytics query with caching"""
        query_key = self._generate_query_key(query_data)
        
        # Check cache first
        cached_result = self._get_cached_result(query_key)
        if cached_result is not None:
            self._update_cache_hit_rate(True)
            return cached_result
        
        self._update_cache_hit_rate(False)
        
        # Execute query
        start_time = time.time()
        
        # Simulate complex analytics processing
        await asyncio.sleep(0.5)  # Simulate processing time
        
        result = {
            'query_id': query_data.get('query_id'),
            'timestamp': datetime.now().isoformat(),
            'processing_time': time.time() - start_time,
            'data': self._generate_mock_analytics_data(query_data),
            'metadata': {
                'source': 'analytics_engine',
                'version': '1.0.0',
                'cached': False
            }
        }
        
        # Cache result
        self._cache_result(query_key, result)
        
        return result
    
    def _generate_query_key(self, query_data: Dict) -> str:
        """Generate cache key for query"""
        # Simple key generation - could be more sophisticated
        key_data = {
            'type': query_data.get('type'),
            'filters': query_data.get('filters', {}),
            'aggregations': query_data.get('aggregations', [])
        }
        return f"query_{hash(json.dumps(key_data, sort_keys=True))}"
    
    def _get_cached_result(self, query_key: str) -> Optional[Dict]:
        """Get cached query result if still valid"""
        if query_key not in self.cache:
            return None
        
        cache_ttl = self.config.settings.get('cache_ttl', 300)  # 5 minutes default
        if time.time() - self.cache_timestamps[query_key] > cache_ttl:
            # Cache expired
            del self.cache[query_key]
            del self.cache_timestamps[query_key]
            return None
        
        result = self.cache[query_key].copy()
        result['metadata']['cached'] = True
        return result
    
    def _cache_result(self, query_key: str, result: Dict) -> None:
        """Cache query result"""
        self.cache[query_key] = result
        self.cache_timestamps[query_key] = time.time()
    
    def _update_cache_hit_rate(self, was_hit: bool) -> None:
        """Update cache hit rate with exponential moving average"""
        alpha = 0.1  # Smoothing factor
        hit_value = 1.0 if was_hit else 0.0
        self.cache_hit_rate = alpha * hit_value + (1 - alpha) * self.cache_hit_rate
    
    def _generate_mock_analytics_data(self, query_data: Dict) -> Dict[str, Any]:
        """Generate mock analytics data for demo purposes"""
        query_type = query_data.get('type', 'standard')
        
        if query_type == 'user_engagement':
            return {
                'total_users': 1250,
                'active_users': 890,
                'sessions': 3420,
                'avg_session_duration': 18.5,
                'bounce_rate': 0.32,
                'trends': {
                    'daily_growth': 0.08,
                    'weekly_growth': 0.15,
                    'monthly_growth': 0.42
                }
            }
        elif query_type == 'performance':
            return {
                'avg_response_time': 145.2,
                'error_rate': 0.003,
                'throughput': 2450,
                'availability': 99.97,
                'bottlenecks': ['database_queries', 'external_api_calls']
            }
        else:
            return {
                'data_points': 500,
                'processed_at': datetime.now().isoformat(),
                'summary': 'Mock analytics data for demonstration'
            }
    
    async def _process_realtime_data(self, data: Dict) -> None:
        """Process real-time data stream"""
        # Simulate real-time processing
        await asyncio.sleep(0.01)
        
        await self.event_bus.emit(
            'analytics.realtime_processed',
            {'data_type': 'realtime', 'processed_count': 1},
            self.config.instance_id
        )
    
    async def _process_batch_data(self, data: Dict) -> None:
        """Process batch data"""
        # Simulate batch processing
        await asyncio.sleep(0.1)
        
        await self.event_bus.emit(
            'analytics.batch_processed',
            {'data_type': 'batch', 'batch_size': data.get('size', 0)},
            self.config.instance_id
        )
    
    async def _process_predictive_data(self, data: Dict) -> None:
        """Process predictive analytics data"""
        # Simulate predictive processing
        await asyncio.sleep(0.2)
        
        await self.event_bus.emit(
            'analytics.prediction_generated',
            {'data_type': 'predictive', 'confidence': 0.85},
            self.config.instance_id
        )
    
    async def _cache_cleanup_loop(self) -> None:
        """Periodic cache cleanup"""
        while self.state == ComponentState.ACTIVE:
            try:
                current_time = time.time()
                cache_ttl = self.config.settings.get('cache_ttl', 300)
                
                expired_keys = [
                    key for key, timestamp in self.cache_timestamps.items()
                    if current_time - timestamp > cache_ttl
                ]
                
                for key in expired_keys:
                    del self.cache[key]
                    del self.cache_timestamps[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                self.analytics.track_error(self.config.instance_id, e, {'operation': 'cache_cleanup'})
                await asyncio.sleep(60)
    
    async def _performance_monitor_loop(self) -> None:
        """Monitor component performance"""
        while self.state == ComponentState.ACTIVE:
            try:
                # Collect performance metrics
                metrics = self._get_performance_metrics()
                
                await self.event_bus.emit(
                    'analytics.performance_update',
                    {'instance_id': self.config.instance_id, 'metrics': metrics},
                    self.config.instance_id
                )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self.analytics.track_error(self.config.instance_id, e, {'operation': 'performance_monitor'})
                await asyncio.sleep(30)
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'cache_size': len(self.cache),
            'cache_hit_rate': round(self.cache_hit_rate, 3),
            'active_queries': len(self.active_queries),
            'uptime': time.time() - (self.start_time or 0),
            'memory_usage': len(str(self.cache)) + len(str(self.active_queries))  # Simplified
        }
    
    async def _cancel_query(self, query_id: str) -> None:
        """Cancel an active query"""
        if query_id in self.active_queries:
            query_info = self.active_queries.pop(query_id)
            duration = time.time() - query_info['start_time']
            
            self.analytics.track_performance(
                self.config.instance_id,
                'query_cancelled',
                duration
            )
            
            await self.event_bus.emit(
                'query.cancelled',
                {'query_id': query_id},
                self.config.instance_id
            )


class WorkflowOrchestrator(BaseComponent):
    """
    Workflow orchestration component that demonstrates:
    - Complex component coordination
    - State machine management
    - Error handling and recovery
    - Dependency management
    """
    
    def __init__(self, metadata, config, event_bus, analytics):
        super().__init__(metadata, config, event_bus, analytics)
        self.workflows = {}
        self.workflow_templates = {}
        
    async def _initialize(self) -> None:
        """Initialize workflow orchestrator"""
        # Load workflow templates
        self.workflow_templates = {
            'data_pipeline': {
                'steps': ['extract', 'transform', 'load', 'validate'],
                'dependencies': {'transform': ['extract'], 'load': ['transform'], 'validate': ['load']},
                'timeout': 300
            },
            'model_training': {
                'steps': ['data_prep', 'feature_engineering', 'train', 'evaluate', 'deploy'],
                'dependencies': {
                    'feature_engineering': ['data_prep'],
                    'train': ['feature_engineering'],
                    'evaluate': ['train'],
                    'deploy': ['evaluate']
                },
                'timeout': 1800
            }
        }
        
        # Subscribe to workflow events
        self.event_bus.subscribe('workflow.start', self._handle_workflow_start)
        self.event_bus.subscribe('workflow.step_completed', self._handle_step_completed)
        self.event_bus.subscribe('workflow.step_failed', self._handle_step_failed)
        
        logger.info(f"Workflow orchestrator initialized with {len(self.workflow_templates)} templates")
    
    async def _start(self) -> None:
        """Start workflow orchestrator"""
        # Start workflow monitoring
        asyncio.create_task(self._workflow_monitor_loop())
        
        await self.event_bus.emit(
            'orchestrator.ready',
            {'instance_id': self.config.instance_id, 'templates': list(self.workflow_templates.keys())},
            self.config.instance_id
        )
    
    async def _stop(self) -> None:
        """Stop workflow orchestrator"""
        # Cancel all running workflows
        for workflow_id in list(self.workflows.keys()):
            await self._cancel_workflow(workflow_id, 'orchestrator_stopping')
    
    async def _destroy(self) -> None:
        """Clean up workflow orchestrator"""
        self.event_bus.unsubscribe('workflow.start', self._handle_workflow_start)
        self.event_bus.unsubscribe('workflow.step_completed', self._handle_step_completed)
        self.event_bus.unsubscribe('workflow.step_failed', self._handle_step_failed)
    
    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow orchestrator settings"""
        validated = {}
        
        if 'max_concurrent_workflows' in settings:
            max_workflows = settings['max_concurrent_workflows']
            if isinstance(max_workflows, int) and max_workflows > 0:
                validated['max_concurrent_workflows'] = min(100, max(1, max_workflows))
        
        if 'default_timeout' in settings:
            timeout = settings['default_timeout']
            if isinstance(timeout, (int, float)) and timeout > 0:
                validated['default_timeout'] = max(60, int(timeout))
        
        return validated
    
    def _on_config_changed(self, old_settings: Dict[str, Any], new_settings: Dict[str, Any]) -> None:
        """Handle configuration changes"""
        if old_settings.get('max_concurrent_workflows') != new_settings.get('max_concurrent_workflows'):
            logger.info(f"Max concurrent workflows updated: {new_settings.get('max_concurrent_workflows')}")
    
    def _get_custom_status(self) -> Dict[str, Any]:
        """Get workflow orchestrator status"""
        workflow_states = {}
        for workflow in self.workflows.values():
            state = workflow['state']
            workflow_states[state] = workflow_states.get(state, 0) + 1
        
        return {
            'active_workflows': len(self.workflows),
            'workflow_states': workflow_states,
            'available_templates': list(self.workflow_templates.keys()),
            'total_steps_executed': sum(len(w.get('completed_steps', [])) for w in self.workflows.values())
        }
    
    async def _handle_workflow_start(self, event: Dict) -> None:
        """Handle workflow start request"""
        data = event.get('data', {})
        workflow_id = data.get('workflow_id')
        template_name = data.get('template')
        
        if not workflow_id or not template_name:
            logger.error("Invalid workflow start request: missing workflow_id or template")
            return
        
        if template_name not in self.workflow_templates:
            await self.event_bus.emit(
                'workflow.failed',
                {'workflow_id': workflow_id, 'error': f'Unknown template: {template_name}'},
                self.config.instance_id
            )
            return
        
        # Check concurrent workflow limits
        max_concurrent = self.config.settings.get('max_concurrent_workflows', 10)
        if len(self.workflows) >= max_concurrent:
            await self.event_bus.emit(
                'workflow.rejected',
                {'workflow_id': workflow_id, 'reason': 'max_concurrent_workflows_exceeded'},
                self.config.instance_id
            )
            return
        
        # Start workflow
        await self._start_workflow(workflow_id, template_name, data.get('parameters', {}))
    
    async def _start_workflow(self, workflow_id: str, template_name: str, parameters: Dict) -> None:
        """Start a new workflow instance"""
        template = self.workflow_templates[template_name]
        
        workflow = {
            'id': workflow_id,
            'template': template_name,
            'state': 'running',
            'start_time': time.time(),
            'parameters': parameters,
            'steps': template['steps'].copy(),
            'dependencies': template['dependencies'].copy(),
            'completed_steps': [],
            'failed_steps': [],
            'current_step': None,
            'timeout': template.get('timeout', self.config.settings.get('default_timeout', 300))
        }
        
        self.workflows[workflow_id] = workflow
        
        # Start first step
        await self._execute_next_step(workflow_id)
        
        await self.event_bus.emit(
            'workflow.started',
            {'workflow_id': workflow_id, 'template': template_name},
            self.config.instance_id
        )
    
    async def _execute_next_step(self, workflow_id: str) -> None:
        """Execute the next available step in the workflow"""
        if workflow_id not in self.workflows:
            return
        
        workflow = self.workflows[workflow_id]
        
        # Find next executable step
        next_step = self._find_next_step(workflow)
        
        if not next_step:
            # No more steps - workflow complete
            await self._complete_workflow(workflow_id)
            return
        
        # Execute step
        workflow['current_step'] = next_step
        step_start_time = time.time()
        
        try:
            # Simulate step execution
            await self._execute_step(workflow_id, next_step, workflow['parameters'])
            
            # Mark step as completed
            workflow['completed_steps'].append(next_step)
            workflow['current_step'] = None
            
            step_duration = time.time() - step_start_time
            self.analytics.track_performance(
                self.config.instance_id,
                f"workflow_step_{next_step}",
                step_duration
            )
            
            await self.event_bus.emit(
                'workflow.step_completed',
                {'workflow_id': workflow_id, 'step': next_step, 'duration': step_duration},
                self.config.instance_id
            )
            
        except Exception as e:
            workflow['failed_steps'].append(next_step)
            workflow['current_step'] = None
            
            self.analytics.track_error(
                self.config.instance_id, 
                e, 
                {'workflow_id': workflow_id, 'step': next_step}
            )
            
            await self.event_bus.emit(
                'workflow.step_failed',
                {'workflow_id': workflow_id, 'step': next_step, 'error': str(e)},
                self.config.instance_id
            )
    
    def _find_next_step(self, workflow: Dict) -> Optional[str]:
        """Find the next step that can be executed"""
        completed = set(workflow['completed_steps'])
        failed = set(workflow['failed_steps'])
        
        for step in workflow['steps']:
            if step in completed or step in failed:
                continue
            
            # Check dependencies
            dependencies = workflow['dependencies'].get(step, [])
            if all(dep in completed for dep in dependencies):
                return step
        
        return None
    
    async def _execute_step(self, workflow_id: str, step: str, parameters: Dict) -> None:
        """Execute a workflow step"""
        # Simulate step execution with different durations
        step_durations = {
            'extract': 0.5,
            'transform': 1.0,
            'load': 0.3,
            'validate': 0.2,
            'data_prep': 0.8,
            'feature_engineering': 1.5,
            'train': 2.0,
            'evaluate': 0.5,
            'deploy': 1.0
        }
        
        duration = step_durations.get(step, 0.5)
        await asyncio.sleep(duration)
        
        # Simulate occasional failures for demo
        if step == 'validate' and parameters.get('simulate_failure'):
            raise Exception(f"Simulated failure in step: {step}")
    
    async def _complete_workflow(self, workflow_id: str) -> None:
        """Complete a workflow"""
        workflow = self.workflows[workflow_id]
        workflow['state'] = 'completed'
        workflow['end_time'] = time.time()
        
        total_duration = workflow['end_time'] - workflow['start_time']
        self.analytics.track_performance(
            self.config.instance_id,
            f"workflow_{workflow['template']}",
            total_duration
        )
        
        await self.event_bus.emit(
            'workflow.completed',
            {
                'workflow_id': workflow_id,
                'template': workflow['template'],
                'duration': total_duration,
                'steps_completed': len(workflow['completed_steps'])
            },
            self.config.instance_id
        )
        
        # Clean up completed workflow after delay
        asyncio.create_task(self._cleanup_workflow(workflow_id, delay=300))
    
    async def _cancel_workflow(self, workflow_id: str, reason: str = 'user_requested') -> None:
        """Cancel a running workflow"""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            workflow['state'] = 'cancelled'
            workflow['end_time'] = time.time()
            
            await self.event_bus.emit(
                'workflow.cancelled',
                {'workflow_id': workflow_id, 'reason': reason},
                self.config.instance_id
            )
            
            # Clean up immediately
            del self.workflows[workflow_id]
    
    async def _cleanup_workflow(self, workflow_id: str, delay: int = 0) -> None:
        """Clean up workflow data after delay"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            logger.debug(f"Cleaned up workflow: {workflow_id}")
    
    async def _handle_step_completed(self, event: Dict) -> None:
        """Handle workflow step completion"""
        data = event.get('data', {})
        workflow_id = data.get('workflow_id')
        
        if workflow_id in self.workflows:
            # Execute next step
            await self._execute_next_step(workflow_id)
    
    async def _handle_step_failed(self, event: Dict) -> None:
        """Handle workflow step failure"""
        data = event.get('data', {})
        workflow_id = data.get('workflow_id')
        
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]
            
            # Check if workflow can continue or should fail
            if len(workflow['failed_steps']) >= 3:  # Max 3 failures
                workflow['state'] = 'failed'
                workflow['end_time'] = time.time()
                
                await self.event_bus.emit(
                    'workflow.failed',
                    {'workflow_id': workflow_id, 'reason': 'too_many_failed_steps'},
                    self.config.instance_id
                )
                
                await self._cleanup_workflow(workflow_id, delay=60)
            else:
                # Try to continue with other steps
                await self._execute_next_step(workflow_id)
    
    async def _workflow_monitor_loop(self) -> None:
        """Monitor workflows for timeouts and health"""
        while self.state == ComponentState.ACTIVE:
            try:
                current_time = time.time()
                
                for workflow_id, workflow in list(self.workflows.items()):
                    # Check for timeouts
                    if workflow['state'] == 'running':
                        elapsed = current_time - workflow['start_time']
                        if elapsed > workflow['timeout']:
                            await self._cancel_workflow(workflow_id, 'timeout')
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.analytics.track_error(self.config.instance_id, e, {'operation': 'workflow_monitor'})
                await asyncio.sleep(30)


async def demo_advanced_components():
    """
    Comprehensive demo of advanced component patterns and interactions.
    """
    print("🚀 Advanced Component System Demo")
    print("=" * 50)
    
    # Create component manager
    manager = create_component_manager()
    
    # Register advanced components
    analytics_metadata = ComponentMetadata(
        id="analytics_panel",
        name="Advanced Analytics Panel",
        version="1.0.0",
        description="Real-time analytics processing with caching and query optimization",
        author="Gary-Zero Framework",
        component_type=ComponentType.PANEL,
        category="analytics",
        tags=["analytics", "real-time", "caching", "queries"],
        permissions=["read_data", "process_data", "cache_data"]
    )
    
    workflow_metadata = ComponentMetadata(
        id="workflow_orchestrator",
        name="Workflow Orchestrator",
        version="1.0.0",
        description="Advanced workflow orchestration with dependency management",
        author="Gary-Zero Framework",
        component_type=ComponentType.SERVICE,
        category="orchestration",
        tags=["workflow", "orchestration", "dependencies", "automation"],
        permissions=["execute_workflows", "manage_pipelines"]
    )
    
    manager.registry.register(AnalyticsPanel, analytics_metadata)
    manager.registry.register(WorkflowOrchestrator, workflow_metadata)
    
    print(f"\n📦 Registered {len(manager.registry.list_components())} components")
    
    # Create component configurations
    analytics_config = ComponentConfig(
        instance_id="analytics_001",
        component_id="analytics_panel",
        user_id="demo_user",
        workspace_id="demo_workspace",
        settings={
            'cache_ttl': 300,
            'query_timeout': 30,
            'max_concurrent_queries': 10
        }
    )
    
    workflow_config = ComponentConfig(
        instance_id="orchestrator_001",
        component_id="workflow_orchestrator",
        user_id="demo_user",
        workspace_id="demo_workspace",
        settings={
            'max_concurrent_workflows': 5,
            'default_timeout': 600
        }
    )
    
    # Create and start components
    print("\n🔧 Creating components...")
    analytics_id = await manager.create_component("analytics_panel", analytics_config)
    orchestrator_id = await manager.create_component("workflow_orchestrator", workflow_config)
    
    print(f"✅ Analytics Panel: {analytics_id}")
    print(f"✅ Workflow Orchestrator: {orchestrator_id}")
    
    # Simulate component interactions
    print("\n⚡ Simulating component interactions...")
    
    # Send data to analytics panel
    await manager.event_bus.emit(
        'data.stream',
        {'type': 'real_time', 'source': 'user_activity', 'data': {'users': 150, 'sessions': 200}},
        'system'
    )
    
    # Send query request
    await manager.event_bus.emit(
        'query.request',
        {
            'query_id': 'query_001',
            'type': 'user_engagement',
            'filters': {'date_range': '7d'},
            'aggregations': ['count', 'avg']
        },
        'user'
    )
    
    # Start a workflow
    await manager.event_bus.emit(
        'workflow.start',
        {
            'workflow_id': 'workflow_001',
            'template': 'data_pipeline',
            'parameters': {'source': 'analytics_db', 'target': 'data_warehouse'}
        },
        'user'
    )
    
    # Wait for interactions to complete
    await asyncio.sleep(3)
    
    # Get component analytics
    print("\n📊 Component Analytics:")
    for instance_id in [analytics_id, orchestrator_id]:
        component = manager.get_component(instance_id)
        status = component.get_status()
        print(f"\n{component.metadata.name}:")
        print(f"  State: {status['state']}")
        print(f"  Uptime: {status['uptime']:.1f}s")
        print(f"  Health Score: {status['analytics']['health_score']:.1f}/100")
        print(f"  Custom Status: {status['custom_status']}")
    
    # System overview
    system_status = manager.get_system_status()
    print(f"\n🖥️  System Status:")
    print(f"  Total Instances: {system_status['total_instances']}")
    print(f"  Event Stats: {system_status['event_stats']['total_events']} events")
    print(f"  Instance States: {system_status['instances_by_state']}")
    
    # Test error handling
    print("\n⚠️  Testing error handling...")
    await manager.event_bus.emit(
        'workflow.start',
        {
            'workflow_id': 'workflow_002',
            'template': 'data_pipeline',
            'parameters': {'simulate_failure': True}
        },
        'user'
    )
    
    await asyncio.sleep(2)
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await manager.destroy_component(analytics_id)
    await manager.destroy_component(orchestrator_id)
    
    print("✅ Advanced demo completed successfully!")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(demo_advanced_components())