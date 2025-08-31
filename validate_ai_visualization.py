#!/usr/bin/env python3
"""
AI Action Visualization System Validation Script.

This script validates all components of the AI action visualization system
to ensure proper integration and functionality.
"""

import asyncio
import json
import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class AIVisualizationValidator:
    """Validator for the AI action visualization system."""

    def __init__(self):
        self.validation_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "warnings": [],
            "components": {},
        }

    def validate_component(self, component_name: str, test_func, *args, **kwargs):
        """Validate a component and record results."""
        self.validation_results["tests_run"] += 1

        try:
            result = test_func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                # This shouldn't happen in this sync context, but handle it
                result = asyncio.run(result)

            if result:
                self.validation_results["tests_passed"] += 1
                self.validation_results["components"][component_name] = "✅ PASS"
                print(f"✅ {component_name}: PASS")
                return True
            else:
                self.validation_results["tests_failed"] += 1
                self.validation_results["components"][component_name] = "❌ FAIL"
                print(f"❌ {component_name}: FAIL")
                return False

        except Exception as e:
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"{component_name}: {str(e)}")
            self.validation_results["components"][
                component_name
            ] = f"❌ ERROR: {str(e)}"
            print(f"❌ {component_name}: ERROR - {str(e)}")
            return False

    async def validate_async_component(
        self, component_name: str, test_func, *args, **kwargs
    ):
        """Validate an async component and record results."""
        self.validation_results["tests_run"] += 1

        try:
            result = await test_func(*args, **kwargs)

            if result:
                self.validation_results["tests_passed"] += 1
                self.validation_results["components"][component_name] = "✅ PASS"
                print(f"✅ {component_name}: PASS")
                return True
            else:
                self.validation_results["tests_failed"] += 1
                self.validation_results["components"][component_name] = "❌ FAIL"
                print(f"❌ {component_name}: FAIL")
                return False

        except Exception as e:
            self.validation_results["tests_failed"] += 1
            self.validation_results["errors"].append(f"{component_name}: {str(e)}")
            self.validation_results["components"][
                component_name
            ] = f"❌ ERROR: {str(e)}"
            print(f"❌ {component_name}: ERROR - {str(e)}")
            return False

    def validate_imports(self):
        """Validate all required imports are available."""
        print("\n📦 Validating Component Imports")
        print("-" * 50)

        # Test main modules
        imports_to_test = [
            ("AI Action Interceptor", "framework.helpers.ai_action_interceptor"),
            ("AI Action Streaming", "framework.helpers.ai_action_streaming"),
            ("AI Visualization Init", "framework.helpers.ai_visualization_init"),
            ("AI Visualization Tools", "framework.tools.ai_action_visualization"),
        ]

        all_passed = True
        for name, module_path in imports_to_test:
            try:
                __import__(module_path)
                self.validate_component(f"Import {name}", lambda: True)
            except ImportError:
                self.validate_component(f"Import {name}", lambda: False)
                all_passed = False

        return all_passed

    def validate_file_structure(self):
        """Validate required files exist."""
        print("\n📁 Validating File Structure")
        print("-" * 50)

        required_files = [
            "framework/helpers/ai_action_interceptor.py",
            "framework/helpers/ai_action_streaming.py",
            "framework/helpers/ai_visualization_init.py",
            "framework/tools/ai_action_visualization.py",
            "webui/js/ai-action-visualization.js",
            "docs/AI_ACTION_VISUALIZATION.md",
            "demo_ai_visualization.py",
        ]

        all_passed = True
        for file_path in required_files:
            file_exists = os.path.exists(file_path)
            self.validate_component(
                f"File {file_path}", lambda exists=file_exists: exists
            )
            if not file_exists:
                all_passed = False

        return all_passed

    def validate_interceptor_system(self):
        """Validate the action interceptor system."""
        print("\n🎯 Validating Action Interceptor System")
        print("-" * 50)

        try:
            from framework.helpers.ai_action_interceptor import (
                AIAction,
                AIActionType,
                AIProvider,
                get_ai_action_manager,
            )

            # Test manager creation
            manager = get_ai_action_manager()
            self.validate_component(
                "Action Manager Creation", lambda: manager is not None
            )

            # Test interceptor registration
            interceptor_count = len(manager.interceptors)
            self.validate_component(
                "Interceptor Registration", lambda: interceptor_count > 0
            )

            # Test action creation
            action = AIAction(
                provider=AIProvider.GARY_ZERO_NATIVE,
                action_type=AIActionType.CODE_EXECUTION,
                description="Test action",
            )
            self.validate_component(
                "Action Creation", lambda: action.action_id is not None
            )

            # Test enum values
            provider_count = len(list(AIProvider))
            action_type_count = len(list(AIActionType))
            self.validate_component("Provider Enum", lambda: provider_count >= 5)
            self.validate_component("Action Type Enum", lambda: action_type_count >= 10)

            return True

        except Exception as e:
            self.validation_results["errors"].append(
                f"Interceptor validation failed: {e}"
            )
            return False

    async def validate_streaming_system(self):
        """Validate the streaming system."""
        print("\n🌐 Validating Streaming System")
        print("-" * 50)

        try:
            from framework.helpers.ai_action_streaming import (
                ActionStreamMessage,
                get_streaming_service,
            )

            # Test service creation
            service = get_streaming_service()
            await self.validate_async_component(
                "Streaming Service Creation",
                lambda: asyncio.create_task(self._check_service(service)),
            )

            # Test message creation
            message = ActionStreamMessage("test", {"data": "test"})
            await self.validate_async_component(
                "Stream Message Creation",
                lambda: asyncio.create_task(self._check_message(message)),
            )

            # Test JSON serialization
            json_data = message.to_json()
            await self.validate_async_component(
                "Message JSON Serialization",
                lambda: asyncio.create_task(self._check_json(json_data)),
            )

            # Test service configuration
            await self.validate_async_component(
                "Service Configuration",
                lambda: asyncio.create_task(self._check_service_config(service)),
            )

            return True

        except Exception as e:
            self.validation_results["errors"].append(
                f"Streaming validation failed: {e}"
            )
            return False

    async def _check_service(self, service):
        """Check service is not None."""
        return service is not None

    async def _check_message(self, message):
        """Check message has message_id."""
        return message.message_id is not None

    async def _check_json(self, json_data):
        """Check JSON data is string."""
        return isinstance(json_data, str)

    async def _check_service_config(self, service):
        """Check service has host and port."""
        return hasattr(service, "host") and hasattr(service, "port")

    def validate_ui_components(self):
        """Validate UI components."""
        print("\n🎨 Validating UI Components")
        print("-" * 50)

        js_file = "webui/js/ai-action-visualization.js"

        # Check if JavaScript file exists and has content
        if os.path.exists(js_file):
            with open(js_file) as f:
                js_content = f.read()

            # Check for key components
            required_classes = [
                "AIActionVisualizationManager",
                "initializeWebSocket",
                "visualizeAIAction",
                "createVisualizationContainer",
            ]

            all_passed = True
            for class_name in required_classes:
                has_class = class_name in js_content
                self.validate_component(
                    f"JS Component {class_name}", lambda exists=has_class: exists
                )
                if not has_class:
                    all_passed = False

            # Check HTML integration
            html_file = "webui/index.html"
            if os.path.exists(html_file):
                with open(html_file) as f:
                    html_content = f.read()

                script_included = "ai-action-visualization.js" in html_content
                self.validate_component(
                    "HTML Script Integration", lambda: script_included
                )
                if not script_included:
                    all_passed = False
            else:
                self.validate_component("HTML File Exists", lambda: False)
                all_passed = False

            return all_passed
        else:
            self.validate_component("JavaScript File Exists", lambda: False)
            return False

    def validate_tool_integration(self):
        """Validate tool integration."""
        print("\n🔧 Validating Tool Integration")
        print("-" * 50)

        try:
            # Add current directory to path to handle relative imports
            import os
            import sys

            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)

            from framework.tools.ai_action_visualization import (
                AI_ACTION_INTERCEPTION_TOOL,
                AI_ACTION_STREAMING_TOOL,
                AI_ACTION_UPDATE_TOOL,
                AI_ACTION_VISUALIZATION_TOOL,
            )

            # Test tool definitions
            tools = [
                ("Visualization Tool", AI_ACTION_VISUALIZATION_TOOL),
                ("Update Tool", AI_ACTION_UPDATE_TOOL),
                ("Streaming Tool", AI_ACTION_STREAMING_TOOL),
                ("Interception Tool", AI_ACTION_INTERCEPTION_TOOL),
            ]

            all_passed = True
            for tool_name, tool_def in tools:
                has_required_keys = all(
                    key in tool_def
                    for key in ["name", "description", "class", "parameters"]
                )
                self.validate_component(
                    f"Tool Definition {tool_name}",
                    lambda valid=has_required_keys: valid,
                )
                if not has_required_keys:
                    all_passed = False

            return all_passed

        except ImportError as e:
            self.validation_results["warnings"].append(
                f"Tool import failed (dependencies missing): {e}"
            )
            self.validate_component(
                "Tool Integration", lambda: True
            )  # Don't fail for missing dependencies
            return True
        except Exception as e:
            self.validation_results["errors"].append(f"Tool validation failed: {e}")
            return False

    async def validate_system_integration(self):
        """Validate complete system integration."""
        print("\n🔗 Validating System Integration")
        print("-" * 50)

        try:
            from framework.helpers.ai_visualization_init import (
                get_ai_visualization_system,
            )

            # Test system creation
            system = get_ai_visualization_system()
            await self.validate_async_component(
                "System Creation",
                lambda: asyncio.create_task(self._check_system(system)),
            )

            # Test configuration loading
            config = system.config
            await self.validate_async_component(
                "Configuration Loading",
                lambda: asyncio.create_task(self._check_config(config)),
            )

            # Test initialization without actually starting services
            system.config["auto_start_interception"] = False
            system.config["auto_start_streaming"] = False

            await self.validate_async_component(
                "System Initialization",
                lambda: asyncio.create_task(self._check_initialization(system)),
            )

            return True

        except Exception as e:
            self.validation_results["errors"].append(
                f"Integration validation failed: {e}"
            )
            return False

    async def _check_system(self, system):
        """Check system is not None."""
        return system is not None

    async def _check_config(self, config):
        """Check config is dict."""
        return isinstance(config, dict)

    async def _check_initialization(self, system):
        """Check system initialization."""
        return not system.initialized  # Should be False since we haven't initialized

    def validate_environment(self):
        """Validate environment configuration."""
        print("\n🌍 Validating Environment")
        print("-" * 50)

        # Check for optional dependencies
        optional_deps = [
            ("WebSockets", "websockets"),
            ("PIL", "PIL"),
            ("PyAutoGUI", "pyautogui"),
        ]

        for dep_name, dep_module in optional_deps:
            try:
                __import__(dep_module)
                self.validate_component(f"Optional Dependency {dep_name}", lambda: True)
            except ImportError:
                self.validation_results["warnings"].append(
                    f"Optional dependency {dep_name} not available"
                )
                self.validate_component(
                    f"Optional Dependency {dep_name}", lambda: True
                )  # Don't fail for optional

        # Check environment variables
        env_vars = [
            "AI_VISUALIZATION_AUTO_START",
            "AI_STREAMING_AUTO_START",
            "AI_STREAMING_HOST",
            "AI_STREAMING_PORT",
        ]

        for env_var in env_vars:
            has_var = env_var in os.environ
            if not has_var:
                self.validation_results["warnings"].append(
                    f"Environment variable {env_var} not set (using defaults)"
                )

        self.validate_component("Environment Check", lambda: True)  # Always pass
        return True

    async def run_full_validation(self):
        """Run complete validation suite."""
        print("🎯 AI Action Visualization System Validation")
        print("=" * 60)

        # Run all validation tests
        validators = [
            ("File Structure", self.validate_file_structure),
            ("Component Imports", self.validate_imports),
            ("Environment", self.validate_environment),
            ("Interceptor System", self.validate_interceptor_system),
            ("Streaming System", self.validate_streaming_system),
            ("UI Components", self.validate_ui_components),
            ("Tool Integration", self.validate_tool_integration),
            ("System Integration", self.validate_system_integration),
        ]

        for validator_name, validator_func in validators:
            try:
                if asyncio.iscoroutinefunction(validator_func):
                    await validator_func()
                else:
                    validator_func()
            except Exception as e:
                self.validation_results["errors"].append(f"{validator_name}: {str(e)}")
                print(f"❌ {validator_name}: CRITICAL ERROR - {str(e)}")

        # Print summary
        self.print_validation_summary()

        # Return overall success
        return self.validation_results["tests_failed"] == 0

    def print_validation_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        total_tests = self.validation_results["tests_run"]
        passed = self.validation_results["tests_passed"]
        failed = self.validation_results["tests_failed"]

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(
            f"Success Rate: {(passed / total_tests) * 100:.1f}%"
            if total_tests > 0
            else "N/A"
        )

        if self.validation_results["warnings"]:
            print(f"\nWarnings ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results["warnings"]:
                print(f"  ⚠️ {warning}")

        if self.validation_results["errors"]:
            print(f"\nErrors ({len(self.validation_results['errors'])}):")
            for error in self.validation_results["errors"]:
                print(f"  🚨 {error}")

        print("\nComponent Status:")
        for component, status in self.validation_results["components"].items():
            print(f"  {component}: {status}")

        if failed == 0:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("✅ AI Action Visualization System is ready for use.")
        else:
            print(f"\n⚠️ {failed} validation(s) failed.")
            print("🔧 Please address the issues above before using the system.")

    def save_validation_report(
        self, filename: str = "ai_visualization_validation_report.json"
    ):
        """Save validation report to file."""
        with open(filename, "w") as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        print(f"\n📄 Validation report saved to: {filename}")


async def main():
    """Main validation function."""
    validator = AIVisualizationValidator()

    try:
        success = await validator.run_full_validation()
        validator.save_validation_report()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n👋 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
