from dataclasses import dataclass
import json
from pathlib import Path

from project_config import ProjectConfig


SUPPORTED_LOOKUP_KEY_SCHEMA_VERSION = 1
SUPPORTED_LOOKUP_KEY_ALGORITHM = "trim-nfc-default-casefold-nfc"
MAX_CODE_POINT = 0x10FFFF
SURROGATE_START = 0xD800
SURROGATE_END = 0xDFFF

HANGUL_S_BASE = 0xAC00
HANGUL_L_BASE = 0x1100
HANGUL_V_BASE = 0x1161
HANGUL_T_BASE = 0x11A7
HANGUL_L_COUNT = 19
HANGUL_V_COUNT = 21
HANGUL_T_COUNT = 28
HANGUL_N_COUNT = HANGUL_V_COUNT * HANGUL_T_COUNT
HANGUL_S_COUNT = HANGUL_L_COUNT * HANGUL_N_COUNT


@dataclass(frozen=True)
class LookupKeyConfig:
    path: Path
    schema_version: int
    unicode_version: str
    algorithm: str
    trim_codepoints: frozenset[int]
    case_folding: dict[int, tuple[int, ...]]
    canonical_decomposition: dict[int, tuple[int, ...]]
    canonical_combining_class: dict[int, int]
    canonical_composition: dict[tuple[int, int], int]

    def normalize(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Lookup-key input must be a string.")
        if any(SURROGATE_START <= ord(char) <= SURROGATE_END for char in value):
            raise ValueError("Lookup-key input must contain only Unicode scalar values.")
        codepoints = [ord(char) for char in value]
        start = 0
        end = len(codepoints)
        while start < end and codepoints[start] in self.trim_codepoints:
            start += 1
        while end > start and codepoints[end - 1] in self.trim_codepoints:
            end -= 1
        normalized = self._normalize_nfc(codepoints[start:end])
        folded: list[int] = []
        for codepoint in normalized:
            folded.extend(self.case_folding.get(codepoint, (codepoint,)))
        return "".join(chr(codepoint) for codepoint in self._normalize_nfc(folded))

    def _normalize_nfc(self, codepoints: list[int]) -> list[int]:
        decomposed: list[int] = []
        for codepoint in codepoints:
            self._decompose(codepoint, decomposed)
        self._reorder_combining_marks(decomposed)
        return self._compose(decomposed)

    def _decompose(self, codepoint: int, output: list[int]) -> None:
        hangul_index = codepoint - HANGUL_S_BASE
        if 0 <= hangul_index < HANGUL_S_COUNT:
            output.append(HANGUL_L_BASE + hangul_index // HANGUL_N_COUNT)
            output.append(HANGUL_V_BASE + (hangul_index % HANGUL_N_COUNT) // HANGUL_T_COUNT)
            trailing_index = hangul_index % HANGUL_T_COUNT
            if trailing_index:
                output.append(HANGUL_T_BASE + trailing_index)
            return
        decomposition = self.canonical_decomposition.get(codepoint)
        if decomposition is None:
            output.append(codepoint)
            return
        for item in decomposition:
            self._decompose(item, output)

    def _reorder_combining_marks(self, codepoints: list[int]) -> None:
        for index in range(1, len(codepoints)):
            combining_class = self.canonical_combining_class.get(codepoints[index], 0)
            if combining_class == 0:
                continue
            cursor = index
            while cursor > 0:
                previous_class = self.canonical_combining_class.get(codepoints[cursor - 1], 0)
                if previous_class == 0 or previous_class <= combining_class:
                    break
                codepoints[cursor - 1], codepoints[cursor] = (
                    codepoints[cursor],
                    codepoints[cursor - 1],
                )
                cursor -= 1

    def _compose_pair(self, first: int, second: int) -> int | None:
        leading_index = first - HANGUL_L_BASE
        if 0 <= leading_index < HANGUL_L_COUNT:
            vowel_index = second - HANGUL_V_BASE
            if 0 <= vowel_index < HANGUL_V_COUNT:
                return HANGUL_S_BASE + (leading_index * HANGUL_V_COUNT + vowel_index) * HANGUL_T_COUNT
        syllable_index = first - HANGUL_S_BASE
        if 0 <= syllable_index < HANGUL_S_COUNT and syllable_index % HANGUL_T_COUNT == 0:
            trailing_index = second - HANGUL_T_BASE
            if 0 < trailing_index < HANGUL_T_COUNT:
                return first + trailing_index
        return self.canonical_composition.get((first, second))

    def _compose(self, codepoints: list[int]) -> list[int]:
        if not codepoints:
            return []
        result = [codepoints[0]]
        starter_position = 0
        starter = codepoints[0]
        last_combining_class = 0
        for codepoint in codepoints[1:]:
            combining_class = self.canonical_combining_class.get(codepoint, 0)
            composite = self._compose_pair(starter, codepoint)
            if composite is not None and (last_combining_class == 0 or last_combining_class < combining_class):
                result[starter_position] = composite
                starter = composite
                continue
            if combining_class == 0:
                starter_position = len(result)
                starter = codepoint
            result.append(codepoint)
            last_combining_class = combining_class
        return result


def _require_mapping(value: object, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Lookup-key registry `{context}` must be a mapping.")
    return value


def _parse_codepoint(value: str, context: str) -> int:
    try:
        codepoint = int(value, 16)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Lookup-key registry `{context}` must be a hexadecimal code point.") from exc
    if not 0 <= codepoint <= MAX_CODE_POINT or (SURROGATE_START <= codepoint <= SURROGATE_END):
        raise ValueError(f"Lookup-key registry `{context}` is not a Unicode scalar value.")
    return codepoint


def _parse_sequence(value: object, context: str) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"Lookup-key registry `{context}` must be a non-empty code-point list.")
    result: list[int] = []
    for index, item in enumerate(value):
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError(f"Lookup-key registry `{context}[{index}]` must be an integer.")
        _parse_codepoint(f"{item:X}", f"{context}[{index}]")
        result.append(item)
    return tuple(result)


def load_lookup_key_config(project: ProjectConfig) -> LookupKeyConfig:
    path = project.lookup_keys_registry
    try:
        data = json.loads(path.read_text(encoding="ascii"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Unable to parse lookup-key registry {path}: {exc}") from exc
    registry = _require_mapping(data, "root")
    unknown_root = set(registry) - {
        "schema_version",
        "unicode_version",
        "algorithm",
        "trim_codepoints",
        "case_folding",
        "canonical_decomposition",
        "canonical_combining_class",
        "canonical_composition",
        "counts",
    }
    if unknown_root:
        raise ValueError(
            "Lookup-key registry root contains unsupported field(s): " + ", ".join(sorted(map(str, unknown_root))) + "."
        )
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_LOOKUP_KEY_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported lookup-key schema_version {schema_version!r}; expected {SUPPORTED_LOOKUP_KEY_SCHEMA_VERSION}."
        )
    unicode_version = registry.get("unicode_version")
    if not isinstance(unicode_version, str) or not unicode_version.strip():
        raise ValueError("Lookup-key registry `unicode_version` must be a non-empty string.")
    algorithm = registry.get("algorithm")
    if algorithm != SUPPORTED_LOOKUP_KEY_ALGORITHM:
        raise ValueError(
            f"Unsupported lookup-key algorithm {algorithm!r}; expected {SUPPORTED_LOOKUP_KEY_ALGORITHM!r}."
        )

    raw_trim = registry.get("trim_codepoints")
    if not isinstance(raw_trim, list):
        raise ValueError("Lookup-key registry `trim_codepoints` must be a code-point list.")
    trim_codepoints = frozenset(
        _parse_sequence([item], f"trim_codepoints[{index}]")[0] for index, item in enumerate(raw_trim)
    )

    def parse_sequence_map(key: str) -> dict[int, tuple[int, ...]]:
        raw = _require_mapping(registry.get(key), key)
        return {
            _parse_codepoint(source, f"{key}.{source}"): _parse_sequence(target, f"{key}.{source}")
            for source, target in raw.items()
        }

    raw_classes = _require_mapping(
        registry.get("canonical_combining_class"),
        "canonical_combining_class",
    )
    combining_classes: dict[int, int] = {}
    for source, value in raw_classes.items():
        if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= 255:
            raise ValueError("Lookup-key registry canonical combining classes must be integers from 1 through 255.")
        combining_classes[_parse_codepoint(source, f"canonical_combining_class.{source}")] = value

    raw_composition = _require_mapping(registry.get("canonical_composition"), "canonical_composition")
    composition: dict[tuple[int, int], int] = {}
    for pair, value in raw_composition.items():
        parts = pair.split("+")
        if len(parts) != 2:
            raise ValueError(f"Lookup-key registry composition key `{pair}` must contain two code points.")
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Lookup-key registry composition `{pair}` must target an integer code point.")
        composition[
            (
                _parse_codepoint(parts[0], f"canonical_composition.{pair}"),
                _parse_codepoint(parts[1], f"canonical_composition.{pair}"),
            )
        ] = _parse_sequence([value], f"canonical_composition.{pair}")[0]

    config = LookupKeyConfig(
        path=path,
        schema_version=schema_version,
        unicode_version=unicode_version.strip(),
        algorithm=algorithm,
        trim_codepoints=trim_codepoints,
        case_folding=parse_sequence_map("case_folding"),
        canonical_decomposition=parse_sequence_map("canonical_decomposition"),
        canonical_combining_class=combining_classes,
        canonical_composition=composition,
    )
    counts = _require_mapping(registry.get("counts"), "counts")
    unknown_counts = set(counts) - {
        "case_folding",
        "canonical_decomposition",
        "canonical_combining_class",
        "canonical_composition",
    }
    if unknown_counts:
        raise ValueError(
            "Lookup-key registry `counts` contains unsupported field(s): "
            + ", ".join(sorted(map(str, unknown_counts)))
            + "."
        )
    actual_counts = {
        "case_folding": len(config.case_folding),
        "canonical_decomposition": len(config.canonical_decomposition),
        "canonical_combining_class": len(config.canonical_combining_class),
        "canonical_composition": len(config.canonical_composition),
    }
    if counts != actual_counts:
        raise ValueError("Lookup-key registry declared counts do not match its mapping data.")
    return config
