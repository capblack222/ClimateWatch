import pytest

from app.config import port_from_env


def test_port_defaults_to_5050_to_avoid_airplay(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    assert port_from_env() == 5050


def test_port_reads_env(monkeypatch):
    monkeypatch.setenv("PORT", "8080")
    assert port_from_env() == 8080


@pytest.mark.parametrize("value", ["abc", "0", "65536", ""])
def test_invalid_port_names_the_setting(monkeypatch, value):
    monkeypatch.setenv("PORT", value)
    with pytest.raises(ValueError, match="PORT must be"):
        port_from_env()
