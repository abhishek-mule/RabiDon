from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Check:
    name: str
    result: str  # pass|warn|fail|not_run|manual_required
    detail: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {"name": self.name, "result": self.result}
        if self.detail:
            d["detail"] = self.detail
        if self.data:
            d["data"] = self.data
        return d


@dataclass
class QaReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, *checks: Check) -> None:
        self.checks.extend(checks)

    @property
    def result(self) -> str:
        results = [c.result for c in self.checks]
        if any(r == "fail" for r in results):
            return "fail"
        if any(r in ("warn", "manual_required") for r in results):
            return "pass_with_warnings"
        return "pass"

    def to_dict(self) -> dict[str, Any]:
        return {"result": self.result, "checks": [c.to_dict() for c in self.checks]}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8")
