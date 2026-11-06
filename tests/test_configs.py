"""Basic sanity tests that do not need Basilisk installed."""
from pathlib import Path
import yaml
import pytest

ROOT = Path(__file__).parents[1]
CONFIGS = sorted((ROOT / "configs").glob("*.yaml"))


@pytest.mark.parametrize("path", CONFIGS, ids=lambda p: p.name)
def test_config_is_valid_yaml(path):
    assert isinstance(yaml.safe_load(path.read_text()), dict)


def test_tle_files_are_three_lines():
    for f in (ROOT / "data" / "tle").glob("*.txt"):
        lines = [ln for ln in f.read_text().splitlines() if ln.strip()]
        assert len(lines) % 3 == 0
        assert all(ln.startswith("1 ") for ln in lines[1::3])
        assert all(ln.startswith("2 ") for ln in lines[2::3])
