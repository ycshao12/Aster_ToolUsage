"""Small host-loop example showing where Aster sits in an agent."""

from aster import AsterPolicy, CandidateAction, SessionLedger, ToolSpec


def lookup_weather(city: str) -> str:
    return f"sunny in {city}"


def main() -> None:
    policy = AsterPolicy(
        [
            ToolSpec(
                name="lookup_weather",
                description="Read current weather for a city.",
                parameters={"city": {"type": "string"}},
                required_parameters=("city",),
            )
        ]
    )
    ledger = SessionLedger()

    call = CandidateAction.tool("lookup_weather", {"city": "Shenzhen"})
    decision = policy.inspect(call, ledger)
    print(decision.kind, decision.reason)
    if decision.accepted and call.tool_call is not None:
        result = lookup_weather(**dict(call.tool_call.arguments))
        policy.observe(call.tool_call, result, ledger=ledger)

    repeated = policy.inspect(call, ledger)
    print(repeated.kind, repeated.reason)


if __name__ == "__main__":
    main()
