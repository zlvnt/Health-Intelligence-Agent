"""
Phase 4a — DeepEval wrappers for metrics A, C, D.
Judge: Claude Haiku 4.5 via custom DeepEvalBaseLLM wrapper.
"""
import json

import anthropic
from deepeval.metrics import GEval, TaskCompletionMetric, ToolCorrectnessMetric
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams, ToolCall
from pydantic import BaseModel

JUDGE_MODEL_ID = "claude-haiku-4-5-20251001"


class AnthropicJudge(DeepEvalBaseLLM):
    def __init__(self):
        self.client = anthropic.Anthropic()

    def get_model_name(self) -> str:
        return JUDGE_MODEL_ID

    def load_model(self):
        return self.client

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> tuple[str, float]:
        if schema:
            response = self.client.messages.create(
                model=JUDGE_MODEL_ID,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            # Parse JSON from response and construct schema object
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Extract JSON block if wrapped in markdown
                import re
                match = re.search(r'\{.*\}', text, re.DOTALL)
                data = json.loads(match.group()) if match else {}
            return schema(**data), 0.0
        else:
            response = self.client.messages.create(
                model=JUDGE_MODEL_ID,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text, 0.0

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None) -> tuple[str, float]:
        return self.generate(prompt, schema)


_judge = AnthropicJudge()


def _applicable(reference_outputs: dict, metric_key: str) -> bool:
    return metric_key in reference_outputs.get("applicable_metrics", ["A", "B", "C", "D", "E"])


def _to_tool_calls(tool_names: list[str]) -> list[ToolCall]:
    return [ToolCall(name=name) for name in tool_names]


def task_completion_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict | None:
    """Metric A — did the agent complete the task?"""
    if not _applicable(reference_outputs, "A"):
        return None

    query = inputs["queries"][-1] if isinstance(inputs.get("queries"), list) else inputs.get("queries", "")
    response = outputs.get("final_response", "")

    test_case = LLMTestCase(
        input=query,
        actual_output=response,
        tools_called=_to_tool_calls(outputs.get("tools_used_flat", [])),
    )
    metric = TaskCompletionMetric(threshold=0.7, model=_judge, include_reason=True)
    metric.measure(test_case)
    return {"key": "task_completion", "score": metric.score, "comment": metric.reason}


def tool_correctness_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict | None:
    """Metric C — were the right tools called?"""
    if not _applicable(reference_outputs, "C"):
        return None

    expected_flat = [
        t for turn in reference_outputs.get("expected_tools_per_turn", [[]])
        for t in turn
    ]
    if not expected_flat:
        return {"key": "tool_correctness", "score": 1.0, "comment": "No required tools"}

    query = inputs["queries"][0] if isinstance(inputs.get("queries"), list) else inputs.get("queries", "")
    response = outputs.get("final_response", "")

    test_case = LLMTestCase(
        input=query,
        actual_output=response,
        tools_called=_to_tool_calls(outputs.get("tools_used_flat", [])),
        expected_tools=_to_tool_calls(expected_flat),
    )
    metric = ToolCorrectnessMetric(model=_judge)
    metric.measure(test_case)
    return {"key": "tool_correctness", "score": metric.score, "comment": getattr(metric, "reason", "")}


def response_quality_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict | None:
    """Metric D — response quality via G-Eval with per-case rubric."""
    if not _applicable(reference_outputs, "D"):
        return None

    rubric = reference_outputs.get("rubric_d")
    if not rubric:
        return None

    query = inputs["queries"][-1] if isinstance(inputs.get("queries"), list) else inputs.get("queries", "")
    response = outputs.get("final_response", "")

    metric = GEval(
        name="ResponseQuality",
        criteria=rubric,
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=_judge,
    )
    test_case = LLMTestCase(input=query, actual_output=response)
    metric.measure(test_case)
    return {"key": "response_quality", "score": metric.score, "comment": metric.reason}
