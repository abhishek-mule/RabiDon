import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_init_creates_db(tmp_path: Path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    env["RABIDON_DB_PATH"] = str(tmp_path / "r.db")
    env["RABIDON_DATA_DIR"] = str(tmp_path / "data")
    env["RABIDON_OUTPUT_DIR"] = str(tmp_path / "out")
    p = subprocess.run([sys.executable, "-m", "rabidon.cli.main", "init"],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["ok"] is True
    assert (tmp_path / "r.db").exists()
