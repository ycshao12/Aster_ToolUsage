"""Public data types used by the Aster runtime guard."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any, Literal

DecisionKind = Literal["accept", "reject", "repair"]
ActionKind = Literal["tool", "final"]


@dataclass(frozen=True)
class ToolSpec:
    """A tool declaration exposed by the host agent."""

    name: str
    description: str = ""
    parameters: Mapping[str, Any] = field(default_factory=dict)
    required_parameters: tuple[str, ...] = ()
    side_effect: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("tool name must be non-empty")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")


@dataclass(frozen=True)
class ToolCall:
    """One candidate tool transition proposed by an agent."""

    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolReceipt:
    """The host's observation after a tool call is executed."""

    call: ToolCall
    result: Any = None
    success: bool = True
    progress_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class PendingRequirement:
    """A state-grounded requirement that must be closed before final output."""

    description: str
    tool_name: str | None = None
    required: bool = True
    resolved: bool = False


@dataclass(frozen=True)
class CandidateAction:
    """A candidate transition presented to Aster for inspection."""

    kind: ActionKind
    tool_call: ToolCall | None = None
    content: str = ""

    @classmethod
    def tool(cls, name: str, arguments: Mapping[str, Any] | None = None) -> "CandidateAction":
        return cls("tool", tool_call=ToolCall(name, dict(arguments or {})))

    @classmethod
    def final(cls, content: str) -> "CandidateAction":
        return cls("final", content=content)


@dataclass(frozen=True)
class Decision:
    """Aster's decision for a candidate action."""

    kind: DecisionKind
    reason: str
    action: CandidateAction
    repair: CandidateAction | None = None

    @property
    def accepted(self) -> bool:
        return self.kind == "accept"
