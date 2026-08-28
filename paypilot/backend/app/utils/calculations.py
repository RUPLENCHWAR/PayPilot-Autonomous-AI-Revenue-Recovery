from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_paise(amount_inr: float) -> int:
    return int(round(float(amount_inr) * 100))


def from_paise(amount_paise: int) -> float:
    return round(amount_paise / 100.0, 2)


def format_inr(amount: float) -> str:
    value = float(amount)
    sign = "-" if value < 0 else ""
    value = abs(value)
    integer, frac = f"{value:.2f}".split(".")
    last_three = integer[-3:]
    rest = integer[:-3]
    if rest:
        parts = []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(parts)) + "," + last_three
    else:
        grouped = last_three
    if frac == "00":
        return f"{sign}₹{grouped}"
    return f"{sign}₹{grouped}.{frac}"


def classify_priority(probability: float) -> str:
    if probability >= 0.80:
        return "HIGH"
    if probability >= 0.60:
        return "MEDIUM"
    return "LOW"


def expected_recovery(amount: float, probability: float) -> float:
    return round(float(amount) * float(probability), 2)
