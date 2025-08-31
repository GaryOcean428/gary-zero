"""Plan evaluation and verification module for the hierarchical planner.

This module provides evaluation loops that verify the output of each subtask before
proceeding. If a subtask fails or returns unexpected results, the plan can adjust
by re-planning or invoking alternative tools.
"""

import json
import logging

from pydantic import BaseModel

from framework.helpers.hierarchical_planner import (
    HierarchicalPlan,
    PlanStatus,
    Subtask,
    SubtaskStatus,
)

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Result of evaluating a subtask's output."""

    success: bool
    score: float  # 0.0 to 1.0
    feedback: str
    suggestions: list[str] = []
    requires_retry: bool = False
    alternative_tool: str | None = None


class EvaluationCriteria(BaseModel):
    """Criteria for evaluating subtask outputs."""

    min_length: int | None = None
    max_length: int | None = None
    required_keywords: list[str] = []
    forbidden_keywords: list[str] = []
    expected_format: str | None = None  # json, markdown, html, etc.
    custom_validator: str | None = None  # custom validation logic


class PlanEvaluator:
    """Evaluates subtask outputs and provides feedback for plan adjustment."""

    def __init__(self):
        """Initialize the plan evaluator."""
        self.evaluation_history: dict[str, list[EvaluationResult]] = {}

    def evaluate_subtask_output(
        self, subtask: Subtask, output: str, criteria: EvaluationCriteria | None = None
    ) -> EvaluationResult:
        """Evaluate the output of a completed subtask.

        Args:
            subtask: The subtask that was executed
            output: The output/result from the subtask
            criteria: Optional evaluation criteria

        Returns:
            EvaluationResult with success status and feedback
        """
        if not output or output.strip() == "":
            return EvaluationResult(
                success=False,
                score=0.0,
                feedback="Subtask produced no output",
                requires_retry=True,
            )

        # Default evaluation logic
        score = 0.5  # Start with neutral score
        feedback_parts = []
        suggestions = []

        # Length-based evaluation
        output_length = len(output.strip())
        if criteria and criteria.min_length and output_length < criteria.min_length:
            score -= 0.2
            feedback_parts.append(
                f"Output too short ({output_length} < {criteria.min_length} chars)"
            )
            suggestions.append("Provide more detailed output")
        elif criteria and criteria.max_length and output_length > criteria.max_length:
            score -= 0.1
            feedback_parts.append(
                f"Output too long ({output_length} > {criteria.max_length} chars)"
            )
            suggestions.append("Provide more concise output")
        else:
            score += 0.1

        # Keyword-based evaluation
        if criteria and criteria.required_keywords:
            missing_keywords = []
            for keyword in criteria.required_keywords:
                if keyword.lower() not in output.lower():
                    missing_keywords.append(keyword)

            if missing_keywords:
                score -= 0.3
                feedback_parts.append(
                    f"Missing required keywords: {', '.join(missing_keywords)}"
                )
                suggestions.append(
                    f"Include information about: {', '.join(missing_keywords)}"
                )
            else:
                score += 0.2

        if criteria and criteria.forbidden_keywords:
            found_forbidden = []
            for keyword in criteria.forbidden_keywords:
                if keyword.lower() in output.lower():
                    found_forbidden.append(keyword)

            if found_forbidden:
                score -= 0.2
                feedback_parts.append(
                    f"Contains forbidden keywords: {', '.join(found_forbidden)}"
                )

        # Format-based evaluation
        if criteria and criteria.expected_format:
            format_valid = self._validate_format(output, criteria.expected_format)
            if format_valid:
                score += 0.2
            else:
                score -= 0.3
                feedback_parts.append(
                    f"Output does not match expected format: {criteria.expected_format}"
                )
                suggestions.append(f"Format output as {criteria.expected_format}")

        # Tool-specific evaluation
        tool_evaluation = self._evaluate_by_tool(subtask, output)
        score += tool_evaluation.score_adjustment
        feedback_parts.extend(tool_evaluation.feedback)
        suggestions.extend(tool_evaluation.suggestions)

        # Normalize score
        score = max(0.0, min(1.0, score))

        # Determine success and retry requirements
        success = score >= 0.7
        requires_retry = score < 0.5

        feedback = (
            "; ".join(feedback_parts)
            if feedback_parts
            else "Output meets basic criteria"
        )

        result = EvaluationResult(
            success=success,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            requires_retry=requires_retry,
            alternative_tool=tool_evaluation.alternative_tool,
        )

        # Store evaluation history
        if subtask.id not in self.evaluation_history:
            self.evaluation_history[subtask.id] = []
        self.evaluation_history[subtask.id].append(result)

        return result

    def _validate_format(self, output: str, expected_format: str) -> bool:
        """Validate output format.

        Args:
            output: The output to validate
            expected_format: Expected format (json, markdown, html, etc.)

        Returns:
            True if format is valid
        """
        output = output.strip()

        if expected_format.lower() == "json":
            try:
                json.loads(output)
                return True
            except json.JSONDecodeError:
                return False

        elif expected_format.lower() == "markdown":
            # Basic markdown validation - check for headers, lists, etc.
            has_markdown = any(
                [
                    output.startswith("#"),
                    "##" in output,
                    "- " in output or "* " in output,
                    "**" in output or "*" in output,
                    "[" in output and "](" in output,
                ]
            )
            return has_markdown

        elif expected_format.lower() == "html":
            # Basic HTML validation
            return "<" in output and ">" in output

        elif expected_format.lower() == "code":
            # Check for code-like patterns
            return any(
                [
                    output.startswith("```"),
                    "def " in output,
                    "function " in output,
                    "import " in output,
                    "from " in output,
                ]
            )

        return True  # Unknown format, assume valid

    def _evaluate_by_tool(
        self, subtask: Subtask, output: str
    ) -> "ToolEvaluationResult":
        """Evaluate output based on the tool that was used.

        Args:
            subtask: The subtask that was executed
            output: The output from the subtask

        Returns:
            ToolEvaluationResult with tool-specific feedback
        """
        tool_name = subtask.tool_name or "unknown"

        if tool_name == "search_engine":
            return self._evaluate_search_output(output)
        elif tool_name == "webpage_content_tool":
            return self._evaluate_webpage_content_output(output)
        elif tool_name == "code_execution_tool":
            return self._evaluate_code_output(output)
        elif tool_name == "knowledge_tool":
            return self._evaluate_knowledge_output(output)
        else:
            return ToolEvaluationResult(
                score_adjustment=0.0, feedback=[], suggestions=[], alternative_tool=None
            )

    def _evaluate_search_output(self, output: str) -> "ToolEvaluationResult":
        """Evaluate search engine output."""
        feedback = []
        suggestions = []
        score_adjustment = 0.0
        alternative_tool = None

        # Check for search result indicators
        if "found" in output.lower() or "results" in output.lower():
            score_adjustment += 0.1
        elif "no results" in output.lower() or "not found" in output.lower():
            score_adjustment -= 0.2
            suggestions.append("Try different search terms")
            alternative_tool = "webpage_content_tool"

        # Check for URLs or links
        if "http" in output or "www." in output:
            score_adjustment += 0.1
        else:
            feedback.append("No URLs found in search results")

        return ToolEvaluationResult(
            score_adjustment=score_adjustment,
            feedback=feedback,
            suggestions=suggestions,
            alternative_tool=alternative_tool,
        )

    def _evaluate_webpage_content_output(self, output: str) -> "ToolEvaluationResult":
        """Evaluate webpage content tool output."""
        feedback = []
        suggestions = []
        score_adjustment = 0.0

        # Check for structured content
        if len(output) > 500:
            score_adjustment += 0.1
        else:
            feedback.append("Retrieved content seems too short")

        # Check for error indicators
        if "error" in output.lower() or "failed" in output.lower():
            score_adjustment -= 0.3
            suggestions.append("Check URL validity or try alternative sources")

        return ToolEvaluationResult(
            score_adjustment=score_adjustment,
            feedback=feedback,
            suggestions=suggestions,
            alternative_tool=None,
        )

    def _evaluate_code_output(self, output: str) -> "ToolEvaluationResult":
        """Evaluate code execution tool output."""
        feedback = []
        suggestions = []
        score_adjustment = 0.0

        # Check for error indicators
        if "error" in output.lower() or "traceback" in output.lower():
            score_adjustment -= 0.4
            suggestions.append("Fix code errors and retry")
        elif "success" in output.lower() or output.strip() != "":
            score_adjustment += 0.2

        return ToolEvaluationResult(
            score_adjustment=score_adjustment,
            feedback=feedback,
            suggestions=suggestions,
            alternative_tool=None,
        )

    def _evaluate_knowledge_output(self, output: str) -> "ToolEvaluationResult":
        """Evaluate knowledge tool output."""
        feedback = []
        suggestions = []
        score_adjustment = 0.0

        # Check for informative content
        if len(output) > 100:
            score_adjustment += 0.1

        # Check for question/answer patterns
        if "?" in output and any(
            word in output.lower() for word in ["answer", "solution", "result"]
        ):
            score_adjustment += 0.1

        return ToolEvaluationResult(
            score_adjustment=score_adjustment,
            feedback=feedback,
            suggestions=suggestions,
            alternative_tool=None,
        )


class ToolEvaluationResult:
    """Result of tool-specific evaluation."""

    def __init__(
        self,
        score_adjustment: float,
        feedback: list[str],
        suggestions: list[str],
        alternative_tool: str | None,
    ):
        self.score_adjustment = score_adjustment
        self.feedback = feedback
        self.suggestions = suggestions
        self.alternative_tool = alternative_tool


class PlanAdjuster:
    """Adjusts plans based on evaluation results and failures."""

    def __init__(self, evaluator: PlanEvaluator):
        """Initialize the plan adjuster.

        Args:
            evaluator: The evaluation engine to use
        """
        self.evaluator = evaluator

    def adjust_plan_after_failure(
        self,
        plan: HierarchicalPlan,
        failed_subtask: Subtask,
        evaluation_result: EvaluationResult,
    ) -> bool:
        """Adjust a plan after a subtask failure.

        Args:
            plan: The plan to adjust
            failed_subtask: The subtask that failed
            evaluation_result: Result from evaluating the failed subtask

        Returns:
            True if plan was successfully adjusted
        """
        logger.info(
            f"Adjusting plan {plan.id} after subtask failure: {failed_subtask.name}"
        )

        # Try alternative tool if suggested
        if evaluation_result.alternative_tool:
            return self._retry_with_alternative_tool(
                plan, failed_subtask, evaluation_result.alternative_tool
            )

        # Split complex subtask into smaller ones
        if len(failed_subtask.description) > 200:
            return self._split_complex_subtask(plan, failed_subtask)

        # Add additional context or preparation subtask
        return self._add_preparation_subtask(plan, failed_subtask)

    def _retry_with_alternative_tool(
        self, plan: HierarchicalPlan, failed_subtask: Subtask, alternative_tool: str
    ) -> bool:
        """Retry a failed subtask with an alternative tool.

        Args:
            plan: The plan to modify
            failed_subtask: The subtask that failed
            alternative_tool: Alternative tool to use

        Returns:
            True if retry was set up successfully
        """
        import uuid

        # Create a new subtask with alternative tool
        retry_subtask = Subtask(
            id=str(uuid.uuid4()),
            name=f"Retry: {failed_subtask.name}",
            description=f"Retry previous task with alternative approach: {failed_subtask.description}",
            tool_name=alternative_tool,
            dependencies=failed_subtask.dependencies.copy(),
        )

        # Insert the retry subtask after the failed one
        failed_index = next(
            i
            for i, subtask in enumerate(plan.subtasks)
            if subtask.id == failed_subtask.id
        )

        plan.subtasks.insert(failed_index + 1, retry_subtask)

        # Update dependencies of subsequent tasks
        for subtask in plan.subtasks[failed_index + 2 :]:
            if failed_subtask.id in subtask.dependencies:
                subtask.dependencies.remove(failed_subtask.id)
                subtask.dependencies.append(retry_subtask.id)

        # Mark original subtask as skipped
        failed_subtask.status = SubtaskStatus.SKIPPED

        logger.info(f"Added retry subtask with tool {alternative_tool}")
        return True

    def _split_complex_subtask(
        self, plan: HierarchicalPlan, failed_subtask: Subtask
    ) -> bool:
        """Split a complex subtask into smaller, more manageable ones.

        Args:
            plan: The plan to modify
            failed_subtask: The complex subtask to split

        Returns:
            True if subtask was successfully split
        """
        import uuid

        # Simple splitting logic based on description
        description = failed_subtask.description

        if "and" in description:
            # Split on "and" conjunctions
            parts = [part.strip() for part in description.split(" and ")]
            if len(parts) > 1:
                new_subtasks = []
                prev_id = None

                for i, part in enumerate(parts):
                    new_subtask = Subtask(
                        id=str(uuid.uuid4()),
                        name=f"{failed_subtask.name} - Part {i + 1}",
                        description=part,
                        tool_name=failed_subtask.tool_name,
                        dependencies=(
                            failed_subtask.dependencies.copy() if i == 0 else [prev_id]
                        ),
                    )
                    new_subtasks.append(new_subtask)
                    prev_id = new_subtask.id

                # Insert new subtasks
                failed_index = next(
                    i
                    for i, subtask in enumerate(plan.subtasks)
                    if subtask.id == failed_subtask.id
                )

                for i, new_subtask in enumerate(new_subtasks):
                    plan.subtasks.insert(failed_index + 1 + i, new_subtask)

                # Update dependencies
                last_new_id = new_subtasks[-1].id
                for subtask in plan.subtasks[failed_index + len(new_subtasks) + 1 :]:
                    if failed_subtask.id in subtask.dependencies:
                        subtask.dependencies.remove(failed_subtask.id)
                        subtask.dependencies.append(last_new_id)

                failed_subtask.status = SubtaskStatus.SKIPPED
                logger.info(f"Split complex subtask into {len(new_subtasks)} parts")
                return True

        return False

    def _add_preparation_subtask(
        self, plan: HierarchicalPlan, failed_subtask: Subtask
    ) -> bool:
        """Add a preparation subtask before the failed one.

        Args:
            plan: The plan to modify
            failed_subtask: The subtask that failed

        Returns:
            True if preparation subtask was added
        """
        import uuid

        prep_subtask = Subtask(
            id=str(uuid.uuid4()),
            name=f"Prepare for: {failed_subtask.name}",
            description=f"Gather necessary information and context for: {failed_subtask.description}",
            tool_name="knowledge_tool",
            dependencies=failed_subtask.dependencies.copy(),
        )

        # Insert preparation subtask before failed one
        failed_index = next(
            i
            for i, subtask in enumerate(plan.subtasks)
            if subtask.id == failed_subtask.id
        )

        plan.subtasks.insert(failed_index, prep_subtask)

        # Update failed subtask dependencies
        failed_subtask.dependencies = [prep_subtask.id]
        failed_subtask.status = SubtaskStatus.PENDING  # Reset to try again

        logger.info(f"Added preparation subtask before {failed_subtask.name}")
        return True


class EvaluationLoop:
    """Main evaluation loop that monitors plan execution and adjusts as needed."""

    def __init__(self):
        """Initialize the evaluation loop."""
        self.evaluator = PlanEvaluator()
        self.adjuster = PlanAdjuster(self.evaluator)

    def process_subtask_completion(
        self,
        plan: HierarchicalPlan,
        subtask: Subtask,
        output: str,
        criteria: EvaluationCriteria | None = None,
    ) -> bool:
        """Process the completion of a subtask with evaluation and potential adjustment.

        Args:
            plan: The plan containing the subtask
            subtask: The completed subtask
            output: The output from the subtask
            criteria: Optional evaluation criteria

        Returns:
            True if subtask was successful, False if plan was adjusted
        """
        # Evaluate the subtask output
        evaluation = self.evaluator.evaluate_subtask_output(subtask, output, criteria)

        if evaluation.success:
            subtask.mark_completed(output)
            logger.info(
                f"Subtask '{subtask.name}' completed successfully (score: {evaluation.score:.2f})"
            )
            return True
        else:
            logger.warning(
                f"Subtask '{subtask.name}' failed evaluation (score: {evaluation.score:.2f}): {evaluation.feedback}"
            )

            if evaluation.requires_retry:
                # Try to adjust the plan
                adjusted = self.adjuster.adjust_plan_after_failure(
                    plan, subtask, evaluation
                )
                if adjusted:
                    logger.info("Plan adjusted after subtask failure")
                    return False
                else:
                    # Mark as failed if adjustment wasn't possible
                    subtask.mark_failed(f"Evaluation failed: {evaluation.feedback}")
                    return False
            else:
                # Accept the output despite low score
                subtask.mark_completed(output)
                logger.info("Subtask completed with low score but accepted")
                return True

    def monitor_plan_execution(self, plan: HierarchicalPlan) -> None:
        """Monitor and evaluate ongoing plan execution.

        Args:
            plan: The plan to monitor
        """
        # This would integrate with the TaskScheduler to monitor task completion
        # and automatically trigger evaluation when subtasks complete

        logger.info(f"Starting monitoring of plan {plan.id}")

        # Check plan status
        if plan.is_complete():
            plan.status = PlanStatus.COMPLETED
            logger.info(f"Plan {plan.id} completed successfully")
        elif plan.has_failed_subtasks():
            plan.status = PlanStatus.FAILED
            logger.warning(f"Plan {plan.id} has failed subtasks")
        else:
            plan.status = PlanStatus.IN_PROGRESS
