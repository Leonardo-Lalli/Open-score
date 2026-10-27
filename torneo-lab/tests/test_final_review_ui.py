"""Browser-independent checks of production UI functions and CSS contrast."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_frontend_pending_count_is_scoped_and_rejects_stale_responses():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js non disponibile")
    subprocess.run([node, str(Path(__file__).with_name("final_review_probe.js"))], check=True, timeout=30)


def test_app_secondary_text_and_status_badges_meet_aa_contrast():
    from test_website import _contrast
    css = (ROOT / "torneo-lab/static/styles.css").read_text(encoding="utf-8")
    muted = re.search(r"--muted:\s*(#[0-9a-f]+);", css)[1]
    for surface in ("#f6f7f2", "#ffffff"):
        assert _contrast(muted, surface) >= 4.5
    for selector in (r"\.tag", r"\.tag\.active", r"\.tag\.completed", r"\.tag\.draft", r"\.tag\.archived"):
        block = re.search(selector + r"\s*\{([^}]+)\}", css)[1]
        fg = re.search(r"(?:^|;)\s*color:\s*(#[0-9a-f]+)", block)[1]
        bg = re.search(r"background:\s*(#[0-9a-f]+)", block)[1]
        assert _contrast(fg, bg) >= 4.5, selector
