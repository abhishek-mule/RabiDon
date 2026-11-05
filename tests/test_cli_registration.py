import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _run(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env["RABIDON_DB_PATH"] = str(tmp_path / "r.db")
    env["RABIDON_DATA_DIR"] = str(tmp_path / "data")
    env["RABIDON_OUTPUT_DIR"] = str(tmp_path / "out")
    return subprocess.run([sys.executable, "-m", "rabidon.cli.main", *args],
                          capture_output=True, text=True, env=env)


@pytest.mark.parametrize("cmd", [
    "worker-run-once", "job-enqueue", "approval-request-create",
    "asset-register", "asset-permit", "video-render-final-local",
    "lead-create", "outreach-draft-create", "outreach-can-send",
    "publish-prepare",
])
def test_help_lists_commands_registered_after_main_guard(cmd: str, tmp_path: Path):
    p = _run(["--help"], tmp_path)
    assert p.returncode == 0, p.stderr
    assert cmd in p.stdout


def test_worker_run_once_and_job_enqueue_registered(tmp_path: Path):
    _run(["init"], tmp_path)
    p = _run(["worker-run-once"], tmp_path)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout) is None
    p2 = _run(["job-enqueue", "build_captions", "--payload-json", json.dumps({"x": 1})], tmp_path)
    assert p2.returncode == 0, p2.stderr
    assert json.loads(p2.stdout)["job_id"] > 0
