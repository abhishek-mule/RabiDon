from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def rupees_to_paise(rupees: str | int | Decimal) -> int:
    # Integer paise only (ADR-008). Use Decimal for parsing to avoid float errors.
    d = Decimal(str(rupees))
    return int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def paise_to_rupees_str(paise: int) -> str:
    d = (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"))
    return format(d, "f")
