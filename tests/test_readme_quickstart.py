"""The README quickstart must be runnable text, not a placeholder wrapper."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_readme_is_not_wrapped_in_stray_quotes():
    text = README.read_text(encoding="utf-8")
    assert not text.startswith("'''")
    assert not text.rstrip("\n").endswith("'''")


def test_readme_has_one_line_maturity_status():
    lines = README.read_text(encoding="utf-8").splitlines()
    status_lines = [line for line in lines if line.startswith("**Status:**")]
    assert len(status_lines) == 1
    assert "Alpha" in status_lines[0]


def test_readme_quickstart_uses_this_repository():
    text = README.read_text(encoding="utf-8")
    quickstart = text.split("### Quick Start (Recommended)", 1)[1]
    quickstart = quickstart.split("### Manual Setup", 1)[0]
    assert "git clone https://github.com/Shards-foundation/revenue-engine.git" in quickstart
    assert "cd revenue-engine" in quickstart
    assert "./scripts/setup.sh" in quickstart
    assert "<repository-url>" not in quickstart
    assert "cd omni-revenue-agent" not in quickstart
    assert "docker-compose up -d" not in quickstart
