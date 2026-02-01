"""Regression tests against golden cases. Fails if behavior regresses."""

import json
from pathlib import Path

from agent.capabilities import Capabilities
from agent.orchestrator import run
from tools.context import FinancialContext
from tools.registry import run_tools


def _load_golden_cases():
    path = Path(__file__).parent / "golden_cases.json"
    with open(path) as f:
        return json.load(f)


def test_golden_same_input_same_output():
    """Same input produces same tool outputs (deterministic)."""
    cases = _load_golden_cases()
    for case in cases[:2]:  # Run first 2
        inp = case["input"]
        ctx = FinancialContext.from_api_input(inp)
        r1, exec1, _ = run_tools(ctx, selected_tool_names=None)
        r2, exec2, _ = run_tools(ctx, selected_tool_names=None)
        assert exec1 == exec2
        dims1 = [x.dimension for x in r1]
        dims2 = [x.dimension for x in r2]
        assert dims1 == dims2


def test_golden_expected_tools():
    """Golden cases: expected tools are executed."""
    cases = _load_golden_cases()
    for case in cases:
        inp = case["input"]
        expected = set(case.get("expected_tools_executed", []))
        if not expected:
            continue
        ctx = FinancialContext.from_api_input(inp)
        _, executed, _ = run_tools(ctx, selected_tool_names=None)
        executed_set = set(executed)
        for tool in expected:
            assert tool in executed_set, f"Case {case['name']}: expected {tool} in {executed}"


def test_golden_no_tool_executed_twice():
    """No tool is executed twice in a single run."""
    cases = _load_golden_cases()
    for case in cases:
        inp = case["input"]
        ctx = FinancialContext.from_api_input(inp)
        _, executed, _ = run_tools(ctx, selected_tool_names=None)
        assert len(executed) == len(set(executed)), f"Case {case['name']}: duplicate tools {executed}"
