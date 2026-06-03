from django.test import TestCase, override_settings

from apps.tasks.models import Task
from apps.tasks.sandbox import evaluate_code_submission
from apps.simulator.services import is_safe_code


class SandboxEvaluationTests(TestCase):
    def test_static_analysis_blocks_dangerous_imports(self):
        is_safe, message = is_safe_code("import os\n")

        self.assertFalse(is_safe)
        self.assertIn("os", message)

    def test_static_analysis_blocks_dangerous_calls(self):
        is_safe, message = is_safe_code("def solve():\n    return open('secret.txt').read()\n")

        self.assertFalse(is_safe)
        self.assertIn("open", message)

    @override_settings(SANDBOX_EXECUTOR="inprocess", SANDBOX_MAX_INSTRUCTIONS=20000)
    def test_safe_code_is_executed_against_all_test_cases(self):
        task = Task.objects.create(
            title="Double value",
            slug="double-value",
            description="Return x * 2.",
            function_name="solve",
            test_input={
                "cases": [
                    {"name": "positive", "input": 3, "expected": 6},
                    {"name": "negative", "input": -4, "expected": -8},
                ]
            },
            expected_output={},
        )

        outcome = evaluate_code_submission("def solve(x):\n    return x * 2\n", task)

        self.assertTrue(outcome.completed)
        self.assertTrue(outcome.is_correct)
        self.assertIsNone(outcome.error_message)

    @override_settings(
        SANDBOX_EXECUTOR="inprocess",
        SANDBOX_MAX_INSTRUCTIONS=20000,
        SANDBOX_COMPARISON_ATOL=0.01,
    )
    def test_numeric_results_allow_small_float_tolerance(self):
        task = Task.objects.create(
            title="Rounded vector",
            slug="rounded-vector",
            description="Return numeric vector.",
            function_name="solve",
            test_input=[],
            expected_output=[1.0, 2.0],
        )

        outcome = evaluate_code_submission("def solve():\n    return [1.004, 1.996]\n", task)

        self.assertTrue(outcome.completed)
        self.assertTrue(outcome.is_correct)
