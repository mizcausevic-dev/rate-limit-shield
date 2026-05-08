"""Minimal demo: protect a flaky LLM call."""
import random
from rate_limit_shield import LLMShield


def fake_llm_call(model: str, prompt: str) -> str:
    """Simulates a 30% failure rate."""
    if random.random() < 0.3:
        raise ConnectionError("upstream 500")
    return f"[{model}] response to: {prompt[:24]}..."


def main() -> None:
    ls = LLMShield(rpm_limits={"gpt-4": 60, "claude-opus": 60})
    shield = ls.shield_for("gpt-4")

    for i in range(5):
        try:
            out = shield.call(fake_llm_call, "gpt-4", f"prompt #{i}")
            print(f"OK {out}")
        except Exception as e:
            print(f"FAIL {type(e).__name__}: {e}")

    print("\nState:", ls.state_snapshot())


if __name__ == "__main__":
    main()
