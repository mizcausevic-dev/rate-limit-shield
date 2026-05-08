from rate_limit_shield import LLMShield, parse_retry_after


def test_parse_retry_after_seconds():
    assert parse_retry_after({"Retry-After": "5"}) == 5.0
    assert parse_retry_after({"retry-after": "12.5"}) == 12.5


def test_parse_retry_after_missing():
    assert parse_retry_after({}) == 0.0
    assert parse_retry_after({"x": "y"}) == 0.0


def test_parse_retry_after_invalid():
    assert parse_retry_after({"Retry-After": "soon"}) == 0.0


def test_per_model_isolation():
    ls = LLMShield(rpm_limits={"gpt-4": 10, "claude-opus": 60})
    a = ls.shield_for("gpt-4")
    b = ls.shield_for("claude-opus")
    assert a is not b
    assert a.bucket.capacity == 10
    assert b.bucket.capacity == 60


def test_state_snapshot():
    ls = LLMShield(rpm_limits={"m1": 30})
    ls.shield_for("m1")
    snap = ls.state_snapshot()
    assert "m1" in snap
    assert snap["m1"]["breaker_state"] == "closed"
