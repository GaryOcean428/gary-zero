#!/usr/bin/env python3
"""
Interactive Demo Script for Gary-Zero Modular Component System

This script demonstrates the complete component system with real-time
interaction and visual feedback, showcasing the "Elevating the Vision"
capabilities.
"""

import asyncio
import json
import time
from datetime import datetime
import logging
from pathlib import Path

# Configure logging for clean demo output
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for demo
    format='%(levelname)s - %(message)s'
)

from .modular_component_system import create_component_manager, ComponentConfig, ComponentMetadata, ComponentType
from .component_examples import AnalyticsPanel, WorkflowOrchestrator


class DemoRunner:
    """Interactive demo runner with real-time feedback"""
    
    def __init__(self):
        self.manager = None
        self.demo_data = {}
        
    async def run_complete_demo(self):
        """Run the complete component system demonstration"""
        print("🎯 Gary-Zero Framework: Elevating the Vision Demo")
        print("=" * 60)
        print("Showcasing the next generation of modular, user-centric design")
        print()
        
        try:
            await self._setup_demo()
            await self._demonstrate_modularity()
            await self._demonstrate_user_experience()
            await self._demonstrate_analytics()
            await self._demonstrate_scalability()
            await self._demonstrate_personalization()
            await self._show_metrics_dashboard()
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            await self._cleanup_demo()
    
    async def _setup_demo(self):
        """Initialize the demo environment"""
        print("🔧 Setting up component system...")
        
        # Create component manager
        self.manager = create_component_manager()
        
        # Register advanced components
        analytics_metadata = ComponentMetadata(
            id="analytics_panel",
            name="Advanced Analytics Panel",
            version="1.0.0",
            description="Real-time analytics processing with intelligent caching",
            author="Gary-Zero Framework",
            component_type=ComponentType.PANEL,
            category="analytics",
            tags=["analytics", "real-time", "intelligence", "insights"],
            permissions=["read_data", "process_data", "cache_data"]
        )
        
        workflow_metadata = ComponentMetadata(
            id="workflow_orchestrator", 
            name="Intelligent Workflow Orchestrator",
            version="1.0.0",
            description="Smart workflow management with predictive optimization",
            author="Gary-Zero Framework",
            component_type=ComponentType.SERVICE,
            category="orchestration",
            tags=["workflow", "automation", "intelligence", "optimization"],
            permissions=["execute_workflows", "manage_pipelines", "optimize_resources"]
        )
        
        self.manager.registry.register(AnalyticsPanel, analytics_metadata)
        self.manager.registry.register(WorkflowOrchestrator, workflow_metadata)
        
        print(f"✅ Registered {len(self.manager.registry.list_components())} component types")
        print()
    
    async def _demonstrate_modularity(self):
        """Demonstrate modular architecture capabilities"""
        print("🧩 Demonstrating Modular Architecture")
        print("-" * 40)
        
        # Show available components
        components = self.manager.registry.list_components()
        print("Available Component Modules:")
        for comp in components:
            print(f"  📦 {comp.name}")
            print(f"     Type: {comp.component_type.value.title()}")
            print(f"     Category: {comp.category}")
            print(f"     Tags: {', '.join(comp.tags)}")
            print()
        
        print("🔗 Component Discovery & Search:")
        
        # Demonstrate search functionality
        search_results = self.manager.registry.search_components("analytics")
        print(f"Search 'analytics': {len(search_results)} results")
        for result in search_results:
            print(f"  • {result.name}")
        
        # Filter by type
        widgets = self.manager.registry.list_components(component_type=ComponentType.WIDGET)
        services = self.manager.registry.list_components(component_type=ComponentType.SERVICE)
        print(f"Widgets: {len(widgets)}, Services: {len(services)}")
        print()
    
    async def _demonstrate_user_experience(self):
        """Demonstrate user experience features"""
        print("✨ Demonstrating Enhanced User Experience")
        print("-" * 40)
        
        # Create personalized component configurations
        user_profiles = {
            "data_analyst": {
                "refresh_interval": 5,
                "cache_ttl": 180,
                "max_concurrent_queries": 15,
                "display_mode": "detailed"
            },
            "executive": {
                "refresh_interval": 30,
                "cache_ttl": 600,
                "max_concurrent_queries": 5,
                "display_mode": "summary"
            },
            "developer": {
                "refresh_interval": 2,
                "cache_ttl": 60,
                "max_concurrent_queries": 25,
                "display_mode": "debug"
            }
        }
        
        print("👤 User Profile-Based Configuration:")
        for profile, settings in user_profiles.items():
            print(f"  {profile.replace('_', ' ').title()}: {settings}")
        
        # Create components with personalized settings
        print("\n🎨 Creating Personalized Component Instances:")
        
        analytics_config = ComponentConfig(
            instance_id="analytics_analyst_001",
            component_id="analytics_panel",
            user_id="data_analyst_user",
            workspace_id="analytics_workspace",
            settings=user_profiles["data_analyst"]
        )
        
        analytics_id = await self.manager.create_component("analytics_panel", analytics_config)
        self.demo_data['analytics_id'] = analytics_id
        
        component = self.manager.get_component(analytics_id)
        print(f"✅ Created: {component.metadata.name}")
        print(f"   Instance: {analytics_id}")
        print(f"   User Profile: Data Analyst")
        print(f"   Optimized for: High-frequency, detailed analysis")
        print()
    
    async def _demonstrate_analytics(self):
        """Demonstrate analytics and monitoring capabilities"""
        print("📊 Demonstrating Real-time Analytics & Monitoring")
        print("-" * 40)
        
        analytics_id = self.demo_data['analytics_id']
        
        # Simulate realistic data streams
        data_streams = [
            {'type': 'real_time', 'source': 'user_activity', 'data': {'active_users': 1847, 'new_sessions': 234}},
            {'type': 'real_time', 'source': 'performance', 'data': {'response_time': 145, 'cpu_usage': 67}},
            {'type': 'batch', 'source': 'daily_metrics', 'data': {'total_transactions': 15678, 'revenue': 234567}},
        ]
        
        print("📡 Simulating Real-time Data Streams:")
        for i, stream in enumerate(data_streams):
            print(f"  Stream {i+1}: {stream['source']} ({stream['type']})")
            await self.manager.event_bus.emit('data.stream', stream, 'data_ingestion_service')
            await asyncio.sleep(0.5)  # Realistic timing
        
        # Simulate user queries
        queries = [
            {'query_id': 'q001', 'type': 'user_engagement', 'priority': 'high'},
            {'query_id': 'q002', 'type': 'performance', 'priority': 'medium'},
            {'query_id': 'q003', 'type': 'user_engagement', 'priority': 'high'},  # Should hit cache
        ]
        
        print("\n🔍 Processing Analytics Queries:")
        for query in queries:
            print(f"  Executing: {query['type']} query (ID: {query['query_id']})")
            await self.manager.event_bus.emit('query.request', query, 'user_interface')
            await asyncio.sleep(0.3)
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Show component analytics
        component = self.manager.get_component(analytics_id)
        status = component.get_status()
        analytics = status['analytics']
        custom = status['custom_status']
        
        print(f"\n📈 Component Performance Metrics:")
        print(f"  Health Score: {analytics['health_score']:.1f}/100")
        print(f"  Cache Hit Rate: {custom['cache_hit_rate']:.1%}")
        print(f"  Active Queries: {custom['active_queries']}")
        print(f"  Total Interactions: {analytics['user_interactions']}")
        print()
    
    async def _demonstrate_scalability(self):
        """Demonstrate scalability and performance under load"""
        print("🚀 Demonstrating Scalability & Performance")
        print("-" * 40)
        
        # Create workflow orchestrator
        workflow_config = ComponentConfig(
            instance_id="orchestrator_demo_001",
            component_id="workflow_orchestrator",
            user_id="system_admin",
            workspace_id="operations_workspace",
            settings={
                'max_concurrent_workflows': 10,
                'default_timeout': 300
            }
        )
        
        orchestrator_id = await self.manager.create_component("workflow_orchestrator", workflow_config)
        self.demo_data['orchestrator_id'] = orchestrator_id
        
        print(f"✅ Created Workflow Orchestrator: {orchestrator_id}")
        
        # Start multiple workflows to demonstrate concurrency
        workflows = [
            {'id': 'wf_001', 'template': 'data_pipeline', 'priority': 'high'},
            {'id': 'wf_002', 'template': 'model_training', 'priority': 'medium'},
            {'id': 'wf_003', 'template': 'data_pipeline', 'priority': 'low'},
        ]
        
        print("\n⚡ Starting Concurrent Workflows:")
        for wf in workflows:
            print(f"  Starting: {wf['template']} workflow (ID: {wf['id']}, Priority: {wf['priority']})")
            await self.manager.event_bus.emit(
                'workflow.start',
                {
                    'workflow_id': wf['id'],
                    'template': wf['template'],
                    'parameters': {'priority': wf['priority']}
                },
                'workflow_scheduler'
            )
            await asyncio.sleep(0.2)
        
        # Monitor workflow progress
        print("\n⏳ Monitoring Workflow Execution:")
        for i in range(6):  # Monitor for 3 seconds
            orchestrator = self.manager.get_component(orchestrator_id)
            status = orchestrator.get_status()
            custom = status['custom_status']
            
            print(f"  Time {i*0.5:.1f}s: {custom['active_workflows']} active workflows, "
                  f"{custom['total_steps_executed']} steps completed")
            await asyncio.sleep(0.5)
        
        print()
    
    async def _demonstrate_personalization(self):
        """Demonstrate personalization and adaptive features"""
        print("🎯 Demonstrating Personalization & Adaptation")
        print("-" * 40)
        
        analytics_id = self.demo_data['analytics_id']
        component = self.manager.get_component(analytics_id)
        
        # Simulate user behavior adaptation
        print("🔄 Adaptive Configuration Based on Usage Patterns:")
        
        # User frequently queries real-time data
        for i in range(5):
            await self.manager.event_bus.emit(
                'query.request',
                {'query_id': f'rt_{i}', 'type': 'real_time_metrics'},
                'user_interface'
            )
            await asyncio.sleep(0.1)
        
        print("  • Detected frequent real-time queries")
        print("  • Adapting cache strategy for real-time data")
        
        # Update component configuration based on "learned" behavior
        original_settings = component.config.settings.copy()
        adaptive_settings = {
            'refresh_interval': 3,  # Faster refresh for real-time user
            'cache_ttl': 30,        # Shorter cache for fresh data
            'real_time_priority': True  # New adaptive setting
        }
        
        component.update_config(adaptive_settings)
        
        print(f"  • Updated refresh interval: {original_settings.get('refresh_interval', 5)}s → {adaptive_settings['refresh_interval']}s")
        print(f"  • Updated cache TTL: {original_settings.get('cache_ttl', 180)}s → {adaptive_settings['cache_ttl']}s")
        print(f"  • Enabled real-time priority mode")
        
        # Demonstrate theme/UI adaptation
        print("\n🎨 UI Theme Adaptation:")
        ui_themes = {
            'data_analyst': {'theme': 'dark', 'density': 'compact', 'charts': 'detailed'},
            'executive': {'theme': 'light', 'density': 'comfortable', 'charts': 'summary'},
            'night_mode': {'theme': 'dark', 'density': 'comfortable', 'charts': 'glowing'}
        }
        
        current_hour = datetime.now().hour
        if 18 <= current_hour or current_hour <= 6:
            selected_theme = ui_themes['night_mode']
            print(f"  🌙 Evening detected - switched to Night Mode theme")
        else:
            selected_theme = ui_themes['data_analyst']
            print(f"  ☀️  Daytime detected - using optimized analyst theme")
        
        print(f"     Theme: {selected_theme['theme']}, Density: {selected_theme['density']}")
        print()
    
    async def _show_metrics_dashboard(self):
        """Show comprehensive metrics dashboard"""
        print("📊 Comprehensive Metrics Dashboard")
        print("-" * 40)
        
        # System-wide metrics
        system_status = self.manager.get_system_status()
        event_stats = self.manager.event_bus.get_event_stats()
        
        print("🖥️  System Overview:")
        print(f"  Total Component Instances: {system_status['total_instances']}")
        print(f"  Registered Component Types: {system_status['registered_components']}")
        print(f"  Total Events Processed: {event_stats['total_events']}")
        print(f"  Active Event Subscriptions: {sum(event_stats['active_subscriptions'].values())}")
        
        print(f"\n📈 Component States:")
        for state, count in system_status['instances_by_state'].items():
            print(f"  {state.title()}: {count}")
        
        print(f"\n⚡ Event Activity:")
        for event_type, count in event_stats['event_counts'].items():
            print(f"  {event_type}: {count} events")
        
        # Individual component metrics
        print(f"\n🔍 Component Analytics:")
        for instance_id in [self.demo_data.get('analytics_id'), self.demo_data.get('orchestrator_id')]:
            if not instance_id:
                continue
                
            component = self.manager.get_component(instance_id)
            if component:
                status = component.get_status()
                analytics = status['analytics']
                
                print(f"\n  📦 {component.metadata.name} ({instance_id[:12]}...)")
                print(f"     Health Score: {analytics['health_score']:.1f}/100")
                print(f"     Uptime: {status['uptime']:.1f}s")
                print(f"     Lifecycle Events: {analytics['lifecycle_events']}")
                print(f"     User Interactions: {analytics['user_interactions']}")
                
                if analytics['performance']:
                    print(f"     Performance Operations:")
                    for op, metrics in analytics['performance'].items():
                        print(f"       {op}: {metrics['avg']:.3f}s avg ({metrics['count']} calls)")
        
        # Demonstrate real-time updates
        print(f"\n🔄 Real-time Monitoring (5 seconds):")
        for i in range(5):
            # Generate some activity
            await self.manager.event_bus.emit(
                'monitoring.heartbeat',
                {'timestamp': datetime.now().isoformat(), 'system_load': 0.65 + i * 0.05},
                'monitoring_service'
            )
            
            current_events = self.manager.event_bus.get_event_stats()['total_events']
            print(f"  Second {i+1}: {current_events} total events processed")
            await asyncio.sleep(1)
        
        print()
    
    async def _cleanup_demo(self):
        """Clean up demo resources"""
        print("🧹 Demo Cleanup")
        print("-" * 40)
        
        cleanup_tasks = []
        
        # Destroy components
        for key in ['analytics_id', 'orchestrator_id']:
            instance_id = self.demo_data.get(key)
            if instance_id:
                component = self.manager.get_component(instance_id)
                if component:
                    print(f"  Destroying: {component.metadata.name}")
                    cleanup_tasks.append(self.manager.destroy_component(instance_id))
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks)
        
        print("✅ All components cleaned up successfully")
        print()
        print("🎉 Demo completed! Gary-Zero Framework showcases:")
        print("   • Modular architecture with intelligent components")
        print("   • Real-time analytics and performance monitoring")
        print("   • Adaptive personalization and user experience")
        print("   • Scalable workflow orchestration")
        print("   • Comprehensive observability and metrics")
        print()
        print("Ready for enterprise deployment! 🚀")


async def run_interactive_demo():
    """Run the interactive demonstration"""
    demo = DemoRunner()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Suppress most logging for clean demo output
    logging.getLogger().setLevel(logging.ERROR)
    
    try:
        asyncio.run(run_interactive_demo())
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()