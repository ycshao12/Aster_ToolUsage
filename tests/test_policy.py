import unittest

from aster import AsterPolicy, CandidateAction, SessionLedger, ToolSpec


class AsterPolicyTests(unittest.TestCase):
    def make_policy(self) -> AsterPolicy:
        return AsterPolicy(
            [
                ToolSpec(
                    name="lookup",
                    parameters={"query": {"type": "string"}},
                    required_parameters=("query",),
                ),
                ToolSpec(
                    name="send_message",
                    parameters={"recipient": {"type": "string"}, "body": {"type": "string"}},
                    required_parameters=("recipient", "body"),
                    side_effect=True,
                ),
            ]
        )

    def test_accepts_declared_call_and_rejects_exact_repeat(self) -> None:
        policy = self.make_policy()
        ledger = SessionLedger()
        action = CandidateAction.tool("lookup", {"query": "weather"})

        self.assertTrue(policy.inspect(action, ledger).accepted)
        policy.observe(action.tool_call, "sunny", ledger=ledger)
        decision = policy.inspect(action, ledger)

        self.assertEqual(decision.kind, "reject")
        self.assertEqual(decision.reason, "repeat_successful_transition")

    def test_rejects_unknown_tool_and_invalid_arguments(self) -> None:
        policy = self.make_policy()
        ledger = SessionLedger()

        self.assertEqual(
            policy.inspect(CandidateAction.tool("search", {}), ledger).reason,
            "undeclared_tool",
        )
        self.assertEqual(
            policy.inspect(CandidateAction.tool("lookup", {}), ledger).reason,
            "missing_required_argument:query",
        )

    def test_final_response_repairs_unresolved_requirement(self) -> None:
        policy = self.make_policy()
        ledger = SessionLedger()
        ledger.add_requirement("send the message", tool_name="send_message")

        decision = policy.inspect(CandidateAction.final("Done."), ledger)

        self.assertEqual(decision.kind, "repair")
        self.assertIsNone(decision.repair)

    def test_failed_receipts_are_not_repeated(self) -> None:
        policy = self.make_policy()
        ledger = SessionLedger()
        action = CandidateAction.tool("lookup", {"query": "weather"})

        policy.observe(action.tool_call, "timeout", success=False, ledger=ledger)
        decision = policy.inspect(action, ledger)

        self.assertEqual(decision.reason, "repeat_failed_transition")


if __name__ == "__main__":
    unittest.main()
