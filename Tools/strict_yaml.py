from datetime import datetime
from pathlib import Path
import copy
import codecs
import re

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode
from yaml.tokens import (
    AliasToken,
    AnchorToken,
    BlockEndToken,
    BlockMappingStartToken,
    BlockSequenceStartToken,
    DocumentEndToken,
    DocumentStartToken,
    FlowMappingEndToken,
    FlowMappingStartToken,
    FlowSequenceEndToken,
    FlowSequenceStartToken,
    ScalarToken,
    TagToken,
)


MAX_YAML_BYTES = 16 * 1024 * 1024
MAX_YAML_DEPTH = 128
MAX_YAML_NODES = 500_000
MAX_YAML_SCALAR_BYTES = 4 * 1024 * 1024

CANONICAL_INTEGER = re.compile(r"^-?(?:0|[1-9][0-9]*)$")
NUMERIC_LIKE = re.compile(
    r"^[+-]?(?:"
    r"[0-9][0-9_]*|"
    r"0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|"
    r"[0-9][0-9_]*(?::[0-9_]+)+|"
    r"(?:[0-9][0-9_]*\.[0-9_]*|\.[0-9_]+)(?:[eE][+-]?[0-9_]+)?|"
    r"[0-9][0-9_]*[eE][+-]?[0-9_]+|"
    r"\.(?:inf|Inf|INF|nan|NaN|NAN)"
    r")$"
)
TIMESTAMP_LIKE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:[Tt ][0-9]{2}:[0-9]{2}:[0-9]{2}.*)?$"
)


RFC3339_PROFILE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})T"
    r"(?P<time>\d{2}:\d{2}:\d{2})(?:\.\d+)?"
    r"(?P<zone>Z|(?P<sign>[+-])(?P<hour>\d{2}):(?P<minute>\d{2}))$"
)


class StrictSafeLoader(yaml.SafeLoader):
    pass


StrictSafeLoader.yaml_implicit_resolvers = copy.deepcopy(
    yaml.SafeLoader.yaml_implicit_resolvers
)
for initial, resolvers in list(StrictSafeLoader.yaml_implicit_resolvers.items()):
    StrictSafeLoader.yaml_implicit_resolvers[initial] = [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag not in {
            "tag:yaml.org,2002:bool",
            "tag:yaml.org,2002:int",
            "tag:yaml.org,2002:float",
            "tag:yaml.org,2002:timestamp",
        }
    ]

StrictSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf")
)
StrictSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:int", CANONICAL_INTEGER, list("-0123456789")
)
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


def decode_yaml_bytes(
    raw: bytes,
    context: str,
    path: Path,
    *,
    max_bytes: int = MAX_YAML_BYTES,
) -> str:
    if len(raw) > max_bytes:
        raise ValueError(
            f"{context.capitalize()} exceeds the {max_bytes}-byte YAML limit: {path}"
        )
    if raw.startswith(codecs.BOM_UTF8):
        raise ValueError(f"{context.capitalize()} must not use a UTF-8 BOM: {path}")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{context.capitalize()} must be valid UTF-8: {path}: {exc}"
        ) from exc


def validate_yaml_source(
    text: str,
    context: str,
    path: Path,
    *,
    max_bytes: int = MAX_YAML_BYTES,
    max_depth: int = MAX_YAML_DEPTH,
    max_nodes: int = MAX_YAML_NODES,
    max_scalar_bytes: int = MAX_YAML_SCALAR_BYTES,
) -> None:
    byte_count = len(text.encode("utf-8"))
    if byte_count > max_bytes:
        raise ValueError(
            f"{context.capitalize()} exceeds the {max_bytes}-byte YAML limit: {path}"
        )

    depth = 0
    node_count = 0
    starts = (
        BlockMappingStartToken,
        BlockSequenceStartToken,
        FlowMappingStartToken,
        FlowSequenceStartToken,
    )
    ends = (BlockEndToken, FlowMappingEndToken, FlowSequenceEndToken)
    try:
        tokens = yaml.scan(text, Loader=StrictSafeLoader)
        for token in tokens:
            if isinstance(token, (AnchorToken, AliasToken, TagToken)):
                raise ValueError(
                    f"{context.capitalize()} uses unsupported YAML anchors, aliases, or tags: {path}"
                )
            if isinstance(token, (DocumentStartToken, DocumentEndToken)):
                raise ValueError(
                    f"{context.capitalize()} must be one implicit YAML document without document markers: {path}"
                )
            if isinstance(token, starts):
                depth += 1
                node_count += 1
                if depth > max_depth:
                    raise ValueError(
                        f"{context.capitalize()} exceeds YAML nesting depth {max_depth}: {path}"
                    )
            elif isinstance(token, ends):
                depth -= 1
            elif isinstance(token, ScalarToken):
                node_count += 1
                scalar_bytes = len(token.value.encode("utf-8"))
                if scalar_bytes > max_scalar_bytes:
                    raise ValueError(
                        f"{context.capitalize()} contains a scalar larger than {max_scalar_bytes} UTF-8 bytes: {path}"
                    )
                if token.style is None:
                    value = token.value
                    if value == "<<":
                        raise ValueError(
                            f"{context.capitalize()} uses unsupported YAML merge keys: {path}"
                        )
                    if value == "~" or (value.lower() == "null" and value != "null"):
                        raise ValueError(
                            f"{context.capitalize()} must use lowercase `null`: {path}"
                        )
                    if value.lower() in {"true", "false"} and value not in {"true", "false"}:
                        raise ValueError(
                            f"{context.capitalize()} must use lowercase Boolean scalars: {path}"
                        )
                    if NUMERIC_LIKE.fullmatch(value) and not CANONICAL_INTEGER.fullmatch(value):
                        raise ValueError(
                            f"{context.capitalize()} contains noncanonical numeric scalar `{value}`: {path}"
                        )
                    if TIMESTAMP_LIKE.fullmatch(value):
                        raise ValueError(
                            f"{context.capitalize()} must quote date and timestamp strings: {path}"
                        )
            if node_count > max_nodes:
                raise ValueError(
                    f"{context.capitalize()} exceeds the {max_nodes}-node YAML limit: {path}"
                )
    except yaml.YAMLError as exc:
        raise ValueError(f"Unable to scan {context} {path}: {exc}") from exc

    try:
        root = yaml.compose(text, Loader=StrictSafeLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Unable to compose {context} {path}: {exc}") from exc
    pending = [root] if root is not None else []
    while pending:
        node = pending.pop()
        if isinstance(node, ScalarNode):
            if node.tag == "tag:yaml.org,2002:null" and node.value == "":
                raise ValueError(
                    f"{context.capitalize()} must write null explicitly as lowercase `null`: {path}"
                )
        elif isinstance(node, MappingNode):
            for key_node, value_node in node.value:
                pending.extend((key_node, value_node))
        elif isinstance(node, SequenceNode):
            pending.extend(node.value)


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
        raw = path.read_bytes()
        text = decode_yaml_bytes(raw, context, path)
        validate_yaml_source(text, context, path)
        data = yaml.load(text, Loader=StrictSafeLoader)
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
    time_parts = tuple(int(part) for part in match.group("time").split(":"))
    if time_parts[0] > 23 or time_parts[1] > 59 or time_parts[2] > 59:
        return False
    hour = match.group("hour")
    minute = match.group("minute")
    if hour is not None:
        if int(minute) > 59:
            return False
        if int(hour) > 14 or (int(hour) == 14 and minute != "00"):
            return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
