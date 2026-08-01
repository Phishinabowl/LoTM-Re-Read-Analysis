from datetime import datetime
from pathlib import Path
import re

import yaml


RFC3339_PROFILE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<time>\d{2}:\d{2}:\d{2})(?:\.\d+)?"
    r"(?P<zone>Z|(?P<sign>[+-])(?P<hour>\d{2}):(?P<minute>\d{2}))$"
)


class StrictSafeLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader: StrictSafeLoader, node, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)


def require_exact_schema_version(
    mapping: dict, expected: int, context: str
) -> int:
    value = mapping.get("schema_version")
    if type(value) is not int or value != expected:
        raise ValueError(
            f"Unsupported {context} schema_version {value!r}; expected integer {expected}."
        )
    return value


def load_yaml_file(
    path: Path, context: str, *, expected_schema_version: int | None = None
):
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"Unable to parse {context} {path}: {exc}") from exc
    if expected_schema_version is not None:
        if not isinstance(data, dict):
            raise ValueError(f"{context.capitalize()} root must be a mapping: {path}")
        require_exact_schema_version(data, expected_schema_version, context)
    return data


def assert_allowed_keys(mapping: dict, allowed: set[str], context: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise ValueError(
            f"{context} contains unsupported field(s): {', '.join(sorted(map(str, unknown)))}."
        )


def is_rfc3339_timestamp(value: str) -> bool:
    match = RFC3339_PROFILE.fullmatch(value)
    if match is None:
        return False
    hour = match.group("hour")
    minute = match.group("minute")
    if hour is not None and (int(hour) > 14 or (int(hour) == 14 and minute != "00")):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
