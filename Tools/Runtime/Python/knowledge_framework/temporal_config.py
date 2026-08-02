from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .schema_pack_config import SchemaPackRegistry
from .strict_yaml import assert_allowed_keys, is_rfc3339_timestamp


MIN_CALENDAR_INSTANT = datetime(1, 1, 1)
MAX_CALENDAR_INSTANT = datetime(9999, 12, 31, 23, 59, 59, 999999)


@dataclass(frozen=True)
class TemporalBound:
    kind: str
    value: str | None
    precision: str | None
    certainty: str | None
    inclusive: bool | None


@dataclass(frozen=True)
class TemporalWindow:
    kind: str
    start: TemporalBound | None
    end: TemporalBound | None


@dataclass(frozen=True)
class TemporalQuery:
    value: str
    precision: str
    lower: datetime
    upper: datetime


TemporalOutcome = Literal[
    "overlap",
    "disjoint",
    "indeterminate-announced",
    "indeterminate-approximate",
    "indeterminate-partial",
    "indeterminate-uncertain",
    "unknown",
]


def _require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping.")
    return value


def _require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string.")
    return value.strip()


def _require_pack_value(packs: SchemaPackRegistry, namespace: str, value: str, context: str) -> None:
    allowed = packs.allowed_values(namespace)
    if not allowed:
        raise ValueError(
            f"Selected schema packs do not provide temporal namespace `{namespace}` required by `{context}`."
        )
    if value not in allowed:
        raise ValueError(f"{context} uses `{value}`, which is not provided in `{namespace}`.")


def parse_temporal_bound(
    value: object,
    context: str,
    packs: SchemaPackRegistry,
) -> TemporalBound:
    bound = _require_mapping(value, context)
    assert_allowed_keys(
        bound,
        {"kind", "value", "precision", "certainty", "inclusive"},
        context,
    )
    kind = _require_string(bound, "kind", context)
    _require_pack_value(packs, "temporal.bound-kind", kind, f"{context}.kind")
    if kind == "unknown":
        extra = set(bound) - {"kind"}
        if extra:
            raise ValueError(f"{context} unknown bounds cannot declare: {', '.join(sorted(extra))}.")
        return TemporalBound(kind, None, None, None, None)
    if kind != "known":
        raise ValueError(f"{context}.kind uses unsupported temporal behavior `{kind}`.")
    raw_value = _require_string(bound, "value", context)
    precision = _require_string(bound, "precision", context)
    certainty = _require_string(bound, "certainty", context)
    inclusive = bound.get("inclusive")
    if type(inclusive) is not bool:
        raise ValueError(f"{context}.inclusive must be true or false.")
    _require_pack_value(packs, "temporal.precision", precision, f"{context}.precision")
    _require_pack_value(packs, "temporal.certainty", certainty, f"{context}.certainty")
    try:
        if precision == "year":
            if not (len(raw_value) == 4 and raw_value.isascii() and raw_value.isdigit()):
                raise ValueError
            datetime(int(raw_value), 1, 1)
        elif precision == "month":
            datetime.strptime(raw_value, "%Y-%m")
        elif precision == "date":
            datetime.strptime(raw_value, "%Y-%m-%d")
        elif precision == "datetime":
            if not is_rfc3339_timestamp(raw_value):
                raise ValueError
        else:
            raise ValueError
    except ValueError as exc:
        raise ValueError(f"{context}.value does not match temporal precision `{precision}`: {raw_value}") from exc
    return TemporalBound(kind, raw_value, precision, certainty, inclusive)


def parse_temporal_window(
    mapping: dict,
    key: str,
    context: str,
    packs: SchemaPackRegistry,
) -> TemporalWindow | None:
    raw_window = mapping.get(key)
    if raw_window is None:
        return None
    window_context = f"{context}.{key}"
    window = _require_mapping(raw_window, window_context)
    assert_allowed_keys(window, {"kind", "start", "end"}, window_context)
    kind = _require_string(window, "kind", window_context)
    _require_pack_value(packs, "temporal.window-kind", kind, f"{window_context}.kind")
    if kind not in {"interval", "unknown"}:
        raise ValueError(f"{window_context}.kind uses unsupported temporal behavior `{kind}`.")
    start = parse_temporal_bound(window["start"], f"{window_context}.start", packs) if "start" in window else None
    end = parse_temporal_bound(window["end"], f"{window_context}.end", packs) if "end" in window else None
    if kind == "unknown":
        if start is not None or end is not None:
            raise ValueError(f"{window_context} unknown windows cannot declare bounds.")
        return TemporalWindow(kind, None, None)
    if start is None and end is None:
        raise ValueError(f"{window_context} interval windows require at least one bound.")
    result = TemporalWindow(kind, start, end)
    lower, upper = temporal_window_limits(result)
    if lower is not None and lower[0] == MAX_CALENDAR_INSTANT and not lower[1]:
        raise ValueError(f"{window_context} has an empty interval beyond the maximum calendar instant.")
    if upper is not None and upper[0] == MIN_CALENDAR_INSTANT and not upper[1]:
        raise ValueError(f"{window_context} has an empty interval before the minimum calendar instant.")
    if lower is not None and upper is not None:
        if lower[0] > upper[0] or (lower[0] == upper[0] and not (lower[1] and upper[1])):
            raise ValueError(f"{window_context} has an empty or reversed interval.")
    return result


def temporal_bound_range(bound: TemporalBound) -> tuple[datetime, datetime]:
    if bound.kind != "known" or bound.value is None or bound.precision is None:
        raise ValueError("Unknown temporal bounds do not have a comparable range.")
    if bound.precision == "year":
        year = int(bound.value)
        return datetime(year, 1, 1), datetime(year, 12, 31, 23, 59, 59, 999999)
    if bound.precision == "month":
        parsed = datetime.strptime(bound.value, "%Y-%m")
        day = calendar.monthrange(parsed.year, parsed.month)[1]
        return parsed, datetime(parsed.year, parsed.month, day, 23, 59, 59, 999999)
    if bound.precision == "date":
        parsed = datetime.strptime(bound.value, "%Y-%m-%d")
        return parsed, parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    parsed = datetime.fromisoformat(bound.value.replace("Z", "+00:00"))
    normalized = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return normalized, normalized


def temporal_window_limits(
    window: TemporalWindow,
) -> tuple[tuple[datetime, bool] | None, tuple[datetime, bool] | None]:
    if window.kind == "unknown":
        return None, None
    lower = None
    upper = None
    if window.start is not None and window.start.kind == "known":
        start_range = temporal_bound_range(window.start)
        lower = (start_range[0] if window.start.inclusive else start_range[1], window.start.inclusive)
    if window.end is not None and window.end.kind == "known":
        end_range = temporal_bound_range(window.end)
        upper = (end_range[1] if window.end.inclusive else end_range[0], window.end.inclusive)
    return lower, upper


def _has_unknown_bound(window: TemporalWindow) -> bool:
    return any(bound is not None and bound.kind == "unknown" for bound in (window.start, window.end))


def _indeterminate_reason(window: TemporalWindow) -> str | None:
    rank = {"announced": 1, "approximate": 2, "uncertain": 3}
    reasons = [
        bound.certainty
        for bound in (window.start, window.end)
        if bound is not None and bound.kind == "known" and bound.certainty in rank
    ]
    if not reasons:
        return None
    certainty = max(reasons, key=lambda item: rank[item])
    return f"indeterminate-{certainty}"


def temporal_overlap_outcome(left: TemporalWindow | None, right: TemporalWindow | None) -> TemporalOutcome:
    if left is None or right is None:
        return "overlap"
    if left.kind == "unknown" or right.kind == "unknown":
        return "unknown"
    left_lower, left_upper = temporal_window_limits(left)
    right_lower, right_upper = temporal_window_limits(right)

    def before(
        upper: tuple[datetime, bool] | None,
        lower: tuple[datetime, bool] | None,
    ) -> bool:
        if upper is None or lower is None:
            return False
        return upper[0] < lower[0] or (upper[0] == lower[0] and not (upper[1] and lower[1]))

    reasons = [reason for reason in (_indeterminate_reason(left), _indeterminate_reason(right)) if reason]
    has_unknown = _has_unknown_bound(left) or _has_unknown_bound(right)
    if has_unknown:
        if reasons:
            return "unknown"
        if before(left_upper, right_lower) or before(right_upper, left_lower):
            return "disjoint"
        return "unknown"
    if reasons:
        rank = {
            "indeterminate-announced": 1,
            "indeterminate-approximate": 2,
            "indeterminate-uncertain": 3,
        }
        return max(reasons, key=lambda item: rank[item])
    if before(left_upper, right_lower) or before(right_upper, left_lower):
        return "disjoint"
    return "overlap"


def temporal_windows_overlap(left: TemporalWindow | None, right: TemporalWindow | None) -> bool:
    return temporal_overlap_outcome(left, right) != "disjoint"


def temporal_match_is_indeterminate(value: str) -> bool:
    return value == "unknown" or value.startswith("indeterminate-")


def normalize_effective_at(
    value: str | datetime | None,
) -> tuple[TemporalQuery | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, datetime):
        parsed = value
        label = value.isoformat()
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return TemporalQuery(label, "datetime", parsed, parsed), label
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Effective time must be an ISO year, month, date, RFC 3339 datetime, or None.")
    label = value.strip()
    precision = None
    if len(label) == 4:
        precision = "year"
    elif len(label) == 7:
        precision = "month"
    elif len(label) == 10:
        precision = "date"
    if precision is not None:
        try:
            lower, upper = temporal_bound_range(TemporalBound("known", label, precision, "exact", True))
        except ValueError as exc:
            raise ValueError("Effective time must be an ISO year, month, date, or RFC 3339 datetime.") from exc
        return TemporalQuery(label, precision, lower, upper), label
    if not is_rfc3339_timestamp(label):
        raise ValueError("Effective time must be an ISO year, month, date, or RFC 3339 datetime.")
    parsed = datetime.fromisoformat(label.replace("Z", "+00:00"))
    normalized = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return TemporalQuery(label, "datetime", normalized, normalized), label


def temporal_window_match(window: TemporalWindow | None, query: TemporalQuery | None) -> str | None:
    if window is None:
        return "unbounded"
    if window.kind == "unknown":
        return "unknown"
    if query is None:
        return None
    lower, upper = temporal_window_limits(window)
    has_unknown = _has_unknown_bound(window)
    reason = _indeterminate_reason(window)
    if has_unknown and reason is not None:
        return "unknown"
    if not has_unknown and reason is not None:
        return reason
    if upper is not None and (upper[0] < query.lower or (upper[0] == query.lower and not upper[1])):
        return None
    if lower is not None and (lower[0] > query.upper or (lower[0] == query.upper and not lower[1])):
        return None
    if has_unknown:
        return "unknown"
    lower_contains = lower is None or query.lower > lower[0] or (query.lower == lower[0] and lower[1])
    upper_contains = upper is None or query.upper < upper[0] or (query.upper == upper[0] and upper[1])
    if not (lower_contains and upper_contains):
        return "indeterminate-partial"
    return "effective"
