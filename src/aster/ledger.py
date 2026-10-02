"""Session ledger for state-grounded tool-use checks."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .types import PendingRequirement, ToolCall, ToolReceipt

_FAILURE_RE = re.compile(
    r"\b(error|failed|failure|exception|invalid|denied|forbidden|"
    r"unauthorized|timeout|unavailable|unable|cannot|blocked)\b",
    re.IGNORECASE,
)


def call_fingerprint(call: ToolCall) -> str:
    """Return a stable identifier for a tool name and JSON-like arguments."""

    encoded = json.dumps(
        {"name": call.name, "arguments": dict(call.arguments)},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass
class SessionLedger:
    """Facts observed during one user-agent interaction.

    The ledger records observations only. It does not infer domain semantics
    from tool names or fabricate a successful result.
    """

    receipts: list[ToolReceipt] = field(default_factory=list)
    requirements: list[PendingRequirement] = field(default_factory=list)

    def record_receipt(self, receipt: ToolReceipt) -> None:
        """Append an observed receipt and resolve matching requirements."""

        self.receipts.append(receipt)
        if not receipt.success:
            return
        observed_name = receipt.call.name
        observed_keys = set(receipt.progress_keys)
        updated: list[PendingRequirement] = []
        for requirement in self.requirements:
            matches_tool = requirement.tool_name in (None, observed_name)
            matches_key = not observed_keys or requirement.description in observed_keys
            resolved = requirement.resolved or (matches_tool and matches_key)
            updated.append(
                PendingRequirement(
                    description=requirement.description,
                    tool_name=requirement.tool_name,
                    required=requirement.required,
                    resolved=resolved,
                )
            )
        self.requirements = updated

    def add_requirement(
        self,
        description: str,
        *,
        tool_name: str | None = None,
        required: bool = True,
    ) -> None:
        """Register a requirement that a final answer must not skip."""

        if not description.strip():
            raise ValueError("requirement description must be non-empty")
        self.requirements.append(
            PendingRequirement(description.strip(), tool_name, required, False)
        )

    def unresolved_requirements(self) -> tuple[PendingRequirement, ...]:
        return tuple(
            item for item in self.requirements if item.required and not item.resolved
        )

    def receipt_for(self, call: ToolCall) -> ToolReceipt | None:
        fingerprint = call_fingerprint(call)
        for receipt in reversed(self.receipts):
            if call_fingerprint(receipt.call) == fingerprint:
                return receipt
        return None

    def validate_arguments(self, call: ToolCall, spec: Any) -> tuple[str, ...]:
        """Validate only executable schema facts for a declared tool."""

        if not isinstance(call.arguments, Mapping):
            return ("arguments_must_be_object",)
        reasons: list[str] = []
        for name in spec.required_parameters:
            if name not in call.arguments or call.arguments[name] in (None, ""):
                reasons.append(f"missing_required_argument:{name}")
        if isinstance(spec.parameters, Mapping):
            allowed = set(spec.parameters)
            reasons.extend(
                f"unexpected_argument:{name}"
                for name in call.arguments
                if allowed and name not in allowed
            )
        return tuple(reasons)

    def repeated_call_reason(self, call: ToolCall) -> str | None:
        previous = self.receipt_for(call)
        if previous is None:
            return None
        if not previous.success or _FAILURE_RE.search(str(previous.result or "")):
            return "repeat_failed_transition"
        if not str(previous.result or "").strip():
            return "repeat_no_progress_transition"
        return "repeat_successful_transition"

    def export(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot for debugging."""

        return {
            "receipts": [
                {
                    "tool": receipt.call.name,
                    "arguments": dict(receipt.call.arguments),
                    "success": receipt.success,
                    "result": receipt.result,
                    "progress_keys": list(receipt.progress_keys),
                }
                for receipt in self.receipts
            ],
            "requirements": [
                {
                    "description": item.description,
                    "tool_name": item.tool_name,
                    "required": item.required,
                    "resolved": item.resolved,
                }
                for item in self.requirements
            ],
        }
