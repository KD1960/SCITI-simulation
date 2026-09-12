import pytest
from pydantic import ValidationError
from sciti.config import load_config, config_hash, Config


def write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text)
    return p


def test_minimal_config_gets_defaults(tmp_path):
    cfg = load_config(write(tmp_path, "name: t\nseed: 3\n"))
    assert cfg.weeks == 156
    assert cfg.decision.policy == "none"
    assert cfg.assumptions.markup["Retail"] == 0.40
    assert cfg.assumptions.satisfaction_weights == {"fill_rate": 0.5, "on_time": 0.3, "quality": 0.2}
    assert cfg.checks.strict is True


def test_unknown_key_is_error(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\nbogus: 1\n"))


def test_unknown_nested_key_is_error(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\ndecision:\n  polcy: rules\n"))


def test_llm_policy_requires_model(tmp_path):
    with pytest.raises(ValidationError):
        load_config(write(tmp_path, "name: t\nseed: 3\ndecision:\n  policy: llm\n"))


def test_hash_stable_and_sensitive():
    a = Config(name="t", seed=1)
    b = Config(name="t", seed=1)
    c = Config(name="t", seed=2)
    assert config_hash(a) == config_hash(b)
    assert config_hash(a) != config_hash(c)
