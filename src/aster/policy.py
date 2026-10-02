"""State-grounded decision checks used by the Aster runtime."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .ledger import SessionLedger
from .types import CandidateAction, Decision, ToolCall, ToolReceipt, ToolSpec


class AsterPolicy:
    """Inspect candidate calls and final responses against current state.

    The host remains responsible for model inference and tool execution. Aster
    is a deterministic guard between a proposed action and the executor.
    """

    def __init__(self, tools: Iterable[ToolSpec]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    @property
    def tools(self) -> tuple[ToolSpec, ...]:
        return tuple(self._tools.values())

    def inspect(self, action: CandidateAction, ledger: SessionLedger) -> Decision:
        if action.kind == "final":
            return self._inspect_final(action, ledger)
        if action.tool_call is None:
            return Decision("reject", "missing_tool_call", action)
        return self._inspect_tool(action, action.tool_call, ledger)

    def _inspect_tool(
        self,
        action: CandidateAction,
        call: ToolCall,
        ledger: SessionLedger,
    ) -> Decision:
        spec = self._tools.get(call.name)
        if spec is None:
            return Decision("reject", "undeclared_tool", action)
        schema_reasons = ledger.validate_arguments(call, spec)
        if schema_reasons:
            return Decision("reject", ";".join(schema_reasons), action)
        repeated_reason = ledger.repeated_call_reason(call)
        if repeated_reason is not None and not spec.side_effect:
            return Decision("reject", repeated_reason, action)
        return Decision("accept", "state_grounded_tool_call", action)

    def _inspect_final(self, action: CandidateAction, ledger: SessionLedger) -> Decision:
        unresolved = ledger.unresolved_requirements()
        if not unresolved:
            return Decision("accept", "no_required_work_remains", action)
        requirement = unresolved[0]
        repair = None
        if requirement.tool_name:
            tool_spec = self._tools.get(requirement.tool_name)
            if tool_spec is not None and not tool_spec.required_parameters:
                repair = CandidateAction.tool(requirement.tool_name, {})
        return Decision(
            "repair",
            f"unresolved_requirement:{requirement.description}",
            action,
            repair,
        )

    def observe(
        self,
        call: ToolCall,
        result: object,
        *,
        success: bool = True,
        progress_keys: Iterable[str] = (),
        ledger: SessionLedger,
    ) -> None:
        """Record a host receipt after execution."""

        ledger.record_receipt(
            ToolReceipt(
                call=call,
                result=result,
                success=success,
                progress_keys=tuple(progress_keys),
            )
        )
