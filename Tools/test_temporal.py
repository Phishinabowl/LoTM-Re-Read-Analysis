import argparse
import json
from pathlib import Path

from project_config import load_project_config
from schema_pack_config import load_schema_pack_registry
from strict_yaml import load_yaml_file
from temporal_config import (
    normalize_effective_at,
    parse_temporal_window,
    temporal_overlap_outcome,
    temporal_window_match,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run domain-neutral temporal conformance tests.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    project = load_project_config(root)
    packs = load_schema_pack_registry(project)
    fixtures = root / "Framework" / "Data" / "Temporal"
    valid = load_yaml_file(fixtures / "valid-windows.yaml", "temporal fixture", expected_schema_version=2)
    windows = {
        window_id: parse_temporal_window(
            {"window": raw}, "window", f"windows.{window_id}", packs
        )
        for window_id, raw in valid["windows"].items()
    }
    malformed = load_yaml_file(fixtures / "invalid-windows.yaml", "temporal fixture", expected_schema_version=2)
    for window_id, raw in malformed["windows"].items():
        try:
            parse_temporal_window({"window": raw}, "window", f"windows.{window_id}", packs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Malformed temporal window was accepted: {window_id}")

    expected = json.loads((fixtures / "expectations.json").read_text(encoding="utf-8"))
    actual_matches = []
    for window_id, effective_at, _ in expected["matches"]:
        query, _ = normalize_effective_at(effective_at)
        outcome = temporal_window_match(windows[window_id], query) or "not-effective"
        actual_matches.append([window_id, effective_at, outcome])
    actual_overlaps = [
        [left, right, temporal_overlap_outcome(windows[left], windows[right])]
        for left, right, _ in expected["overlaps"]
    ]
    if actual_matches != expected["matches"]:
        raise AssertionError(f"Temporal match vectors differ: {actual_matches}")
    if actual_overlaps != expected["overlaps"]:
        raise AssertionError(f"Temporal overlap vectors differ: {actual_overlaps}")
    print(
        f"Temporal conformance passed: {len(windows)} valid windows, "
        f"{len(malformed['windows'])} malformed windows, "
        f"{len(actual_matches)} match and {len(actual_overlaps)} overlap vectors."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
