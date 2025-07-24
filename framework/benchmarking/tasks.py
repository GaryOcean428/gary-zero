"""
Standard benchmark tasks for GAIA-style evaluation.

Provides a collection of standardized tasks for evaluating agent capabilities
across different domains and complexity levels.
"""

import json
from pathlib import Path

from .harness import TaskType, TestCase


class TaskRegistry:
    """Registry for managing benchmark tasks."""

    def __init__(self):
        self.tasks: dict[str, TestCase] = {}
        self.task_groups: dict[str, list[str]] = {}

    def register_task(self, task: TestCase, group: str | None = None) -> None:
        """Register a task in the registry."""
        self.tasks[task.task_id] = task

        if group:
            if group not in self.task_groups:
                self.task_groups[group] = []
            self.task_groups[group].append(task.task_id)

    def get_task(self, task_id: str) -> TestCase | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_tasks_by_group(self, group: str) -> list[TestCase]:
        """Get all tasks in a group."""
        task_ids = self.task_groups.get(group, [])
        return [self.tasks[task_id] for task_id in task_ids if task_id in self.tasks]

    def get_tasks_by_type(self, task_type: TaskType) -> list[TestCase]:
        """Get all tasks of a specific type."""
        return [task for task in self.tasks.values() if task.task_type == task_type]

    def list_tasks(self) -> list[str]:
        """List all task IDs."""
        return list(self.tasks.keys())

    def list_groups(self) -> list[str]:
        """List all task groups."""
        return list(self.task_groups.keys())


class StandardTasks:
    """Collection of standard benchmark tasks."""

    @staticmethod
    def create_summarization_tasks() -> list[TestCase]:
        """Create text summarization benchmark tasks."""
        return [
            TestCase(
                task_id="summarize_research_paper",
                name="Research Paper Summarization",
                description="Summarize a scientific research paper into key findings",
                task_type=TaskType.SUMMARIZATION,
                input_data={
                    "text": """Abstract: Large language models (LLMs) have shown remarkable capabilities across various natural language processing tasks. However, their performance on complex reasoning tasks remains limited by their training data and architectural constraints. This paper introduces a novel approach to enhance reasoning capabilities through multi-step prompting and verification mechanisms.

Introduction: Recent advances in transformer-based language models have demonstrated impressive performance on language understanding and generation tasks. Models like GPT-3 and PaLM have shown emergent abilities in few-shot learning and complex reasoning. However, these models still struggle with multi-step reasoning tasks that require maintaining coherent logical chains over extended contexts.

Methods: We propose a framework that combines chain-of-thought prompting with self-verification mechanisms. Our approach breaks down complex reasoning tasks into smaller, verifiable steps, allowing the model to check its own work at each stage. We evaluate this method on mathematical reasoning, logical inference, and causal reasoning benchmarks.

Results: Our approach shows significant improvements over baseline prompting methods. On the GSM8K mathematical reasoning benchmark, we achieve a 15% improvement in accuracy. On logical reasoning tasks, the improvement reaches 23%. The self-verification mechanism reduces error propagation by catching mistakes early in the reasoning chain.

Conclusion: Multi-step prompting with verification represents a promising direction for enhancing LLM reasoning capabilities. Future work should explore more sophisticated verification mechanisms and their application to other cognitive tasks.""",
                    "max_length": 150,
                    "format": "bullet_points",
                },
                expected_output={
                    "summary": "• LLMs show limitations in complex reasoning despite their general capabilities\n• New framework combines chain-of-thought prompting with self-verification\n• Method breaks reasoning into verifiable steps to reduce error propagation\n• Significant improvements: 15% on math tasks, 23% on logical reasoning\n• Self-verification mechanism catches mistakes early in reasoning chains"
                },
                scoring_criteria={
                    "accuracy": 0.4,  # Factual correctness
                    "completeness": 0.3,  # Coverage of key points
                    "conciseness": 0.2,  # Appropriate length
                    "clarity": 0.1,  # Readability
                },
                timeout_seconds=120,
            ),
            TestCase(
                task_id="summarize_news_article",
                name="News Article Summarization",
                description="Create a concise summary of a news article",
                task_type=TaskType.SUMMARIZATION,
                input_data={
                    "text": """Technology companies are facing increased scrutiny over their data collection practices as new privacy regulations come into effect worldwide. The European Union's General Data Protection Regulation (GDPR), implemented in 2018, set a precedent for stricter data protection laws globally.

Recent developments include California's Consumer Privacy Act (CCPA) and similar legislation proposed in several other US states. These laws give consumers more control over their personal data, including the right to know what information is collected, the right to delete personal information, and the right to opt-out of data sales.

Tech giants like Google, Facebook, and Apple have had to make significant changes to their data collection and processing practices. This includes implementing new consent mechanisms, providing clearer privacy policies, and developing tools that allow users to download or delete their data.

The financial impact has been substantial, with companies spending billions on compliance efforts. However, some experts argue that these regulations may ultimately benefit larger companies by creating barriers to entry for smaller competitors who cannot afford extensive compliance infrastructure.

Consumer advocacy groups generally support these measures, arguing that they restore some balance between corporate interests and individual privacy rights. However, some business organizations warn that overly strict regulations could stifle innovation and economic growth.""",
                    "max_length": 100,
                    "format": "paragraph",
                },
                expected_output={
                    "summary": "New privacy regulations like GDPR and CCPA are forcing tech companies to change their data practices, giving consumers more control over personal information. While compliance costs are substantial and may favor larger companies, consumer advocates support these measures as necessary for protecting privacy rights."
                },
                scoring_criteria={
                    "accuracy": 0.5,
                    "completeness": 0.3,
                    "conciseness": 0.2,
                },
                timeout_seconds=90,
            ),
        ]

    @staticmethod
    def create_code_generation_tasks() -> list[TestCase]:
        """Create code generation benchmark tasks."""
        return [
            TestCase(
                task_id="generate_sorting_algorithm",
                name="Sorting Algorithm Implementation",
                description="Implement a sorting algorithm with proper error handling",
                task_type=TaskType.CODE_GENERATION,
                input_data={
                    "language": "python",
                    "requirements": [
                        "Implement quicksort algorithm",
                        "Handle empty arrays",
                        "Include input validation",
                        "Add docstring with complexity analysis",
                        "Include at least 3 test cases",
                    ],
                    "constraints": {
                        "max_lines": 50,
                        "must_include": ["def", "docstring", "test"],
                    },
                },
                expected_output={
                    "code": """def quicksort(arr):
    \"\"\"
    Sorts an array using the quicksort algorithm.
    
    Time Complexity: O(n log n) average, O(n²) worst case
    Space Complexity: O(log n) average
    
    Args:
        arr: List of comparable elements
        
    Returns:
        Sorted list
        
    Raises:
        TypeError: If input is not a list
    \"\"\"
    if not isinstance(arr, list):
        raise TypeError("Input must be a list")
    
    if len(arr) <= 1:
        return arr.copy()
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)

# Test cases
test_cases = [
    [],
    [1],
    [3, 1, 4, 1, 5, 9, 2, 6],
    ["c", "a", "b"]
]

for test in test_cases:
    print(f"Input: {test}")
    print(f"Output: {quicksort(test)}")
    print()""",
                    "language": "python",
                },
                scoring_criteria={
                    "correctness": 0.4,  # Algorithm works correctly
                    "completeness": 0.3,  # Meets all requirements
                    "code_quality": 0.2,  # Clean, readable code
                    "documentation": 0.1,  # Good docstrings/comments
                },
                timeout_seconds=300,
            ),
            TestCase(
                task_id="generate_api_client",
                name="REST API Client",
                description="Generate a simple REST API client class",
                task_type=TaskType.CODE_GENERATION,
                input_data={
                    "language": "python",
                    "requirements": [
                        "Create a RESTClient class",
                        "Support GET, POST, PUT, DELETE methods",
                        "Include error handling",
                        "Support custom headers",
                        "Include timeout handling",
                    ],
                    "api_base_url": "https://api.example.com",
                    "constraints": {
                        "max_lines": 80,
                        "libraries_allowed": ["requests", "json", "time"],
                    },
                },
                scoring_criteria={
                    "functionality": 0.4,
                    "error_handling": 0.3,
                    "code_structure": 0.2,
                    "documentation": 0.1,
                },
                timeout_seconds=240,
            ),
        ]

    @staticmethod
    def create_presentation_tasks() -> list[TestCase]:
        """Create presentation generation benchmark tasks."""
        return [
            TestCase(
                task_id="create_tech_presentation",
                name="Technology Presentation",
                description="Create a presentation outline about emerging technology",
                task_type=TaskType.PRESENTATION_CREATION,
                input_data={
                    "topic": "Artificial Intelligence in Healthcare",
                    "audience": "Hospital administrators and medical staff",
                    "duration": "20 minutes",
                    "slides_count": 10,
                    "requirements": [
                        "Executive summary",
                        "Current challenges in healthcare",
                        "AI solutions and benefits",
                        "Implementation considerations",
                        "Case studies or examples",
                        "Cost-benefit analysis",
                        "Timeline for adoption",
                        "Q&A preparation",
                    ],
                },
                expected_output={
                    "outline": {
                        "slides": [
                            {
                                "title": "AI in Healthcare: Transforming Patient Care",
                                "content": "Overview and agenda",
                            },
                            {
                                "title": "Executive Summary",
                                "content": "Key benefits and ROI of AI implementation",
                            },
                            {
                                "title": "Current Healthcare Challenges",
                                "content": "Staff shortages, diagnostic errors, cost pressures",
                            },
                            {
                                "title": "AI Solutions Overview",
                                "content": "Diagnostic imaging, predictive analytics, personalized treatment",
                            },
                            {
                                "title": "Benefits and Outcomes",
                                "content": "Improved accuracy, efficiency gains, cost reduction",
                            },
                            {
                                "title": "Implementation Roadmap",
                                "content": "Phases, timeline, resource requirements",
                            },
                            {
                                "title": "Case Study: Radiology AI",
                                "content": "Real-world implementation and results",
                            },
                            {
                                "title": "Cost-Benefit Analysis",
                                "content": "Investment requirements and expected ROI",
                            },
                            {
                                "title": "Next Steps",
                                "content": "Action items and decision points",
                            },
                            {
                                "title": "Q&A Discussion",
                                "content": "Common questions and concerns",
                            },
                        ]
                    }
                },
                scoring_criteria={
                    "relevance": 0.3,  # Appropriate for audience
                    "completeness": 0.3,  # Covers all requirements
                    "structure": 0.2,  # Logical flow
                    "practicality": 0.2,  # Actionable insights
                },
                timeout_seconds=180,
            )
        ]

    @staticmethod
    def create_research_tasks() -> list[TestCase]:
        """Create research analysis benchmark tasks."""
        return [
            TestCase(
                task_id="analyze_market_trends",
                name="Market Trend Analysis",
                description="Analyze market trends from provided data",
                task_type=TaskType.RESEARCH_ANALYSIS,
                input_data={
                    "data": {
                        "sales_data": {
                            "Q1_2023": {
                                "revenue": 1200000,
                                "units": 15000,
                                "growth": 0.12,
                            },
                            "Q2_2023": {
                                "revenue": 1350000,
                                "units": 16200,
                                "growth": 0.125,
                            },
                            "Q3_2023": {
                                "revenue": 1280000,
                                "units": 15800,
                                "growth": -0.05,
                            },
                            "Q4_2023": {
                                "revenue": 1450000,
                                "units": 17500,
                                "growth": 0.13,
                            },
                        },
                        "market_factors": [
                            "Increased competition from new entrants",
                            "Supply chain disruptions in Q3",
                            "Holiday season boost in Q4",
                            "Economic uncertainty affecting consumer spending",
                        ],
                    },
                    "analysis_requirements": [
                        "Identify key trends and patterns",
                        "Explain quarterly variations",
                        "Provide recommendations for next year",
                        "Assess risk factors",
                    ],
                },
                scoring_criteria={
                    "insight_quality": 0.4,
                    "data_interpretation": 0.3,
                    "recommendations": 0.2,
                    "presentation": 0.1,
                },
                timeout_seconds=240,
            )
        ]

    @staticmethod
    def get_all_standard_tasks() -> TaskRegistry:
        """Get a registry with all standard tasks."""
        registry = TaskRegistry()

        # Register summarization tasks
        for task in StandardTasks.create_summarization_tasks():
            registry.register_task(task, "summarization")

        # Register code generation tasks
        for task in StandardTasks.create_code_generation_tasks():
            registry.register_task(task, "code_generation")

        # Register presentation tasks
        for task in StandardTasks.create_presentation_tasks():
            registry.register_task(task, "presentation")

        # Register research tasks
        for task in StandardTasks.create_research_tasks():
            registry.register_task(task, "research")

        return registry

    @staticmethod
    def load_tasks_from_file(file_path: str) -> TaskRegistry:
        """Load tasks from a JSON file."""
        registry = TaskRegistry()

        with open(file_path) as f:
            data = json.load(f)

        for task_data in data.get("tasks", []):
            task = TestCase(
                task_id=task_data["task_id"],
                name=task_data["name"],
                description=task_data["description"],
                task_type=TaskType(task_data["task_type"]),
                input_data=task_data["input_data"],
                expected_output=task_data.get("expected_output"),
                ground_truth=task_data.get("ground_truth"),
                reference_files=task_data.get("reference_files", []),
                timeout_seconds=task_data.get("timeout_seconds", 300),
                max_retries=task_data.get("max_retries", 0),
                scoring_criteria=task_data.get("scoring_criteria", {}),
                metadata=task_data.get("metadata", {}),
            )

            group = task_data.get("group")
            registry.register_task(task, group)

        return registry

    @staticmethod
    def save_tasks_to_file(registry: TaskRegistry, file_path: str) -> None:
        """Save tasks to a JSON file."""
        data = {"tasks": []}

        for task_id, task in registry.tasks.items():
            # Find the group for this task
            group = None
            for group_name, task_ids in registry.task_groups.items():
                if task_id in task_ids:
                    group = group_name
                    break

            task_data = {
                "task_id": task.task_id,
                "name": task.name,
                "description": task.description,
                "task_type": task.task_type.value,
                "input_data": task.input_data,
                "expected_output": task.expected_output,
                "ground_truth": task.ground_truth,
                "reference_files": task.reference_files,
                "timeout_seconds": task.timeout_seconds,
                "max_retries": task.max_retries,
                "scoring_criteria": task.scoring_criteria,
                "metadata": task.metadata,
                "group": group,
            }

            data["tasks"].append(task_data)

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
