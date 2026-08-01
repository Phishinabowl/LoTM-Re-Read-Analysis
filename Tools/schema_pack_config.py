from dataclasses import dataclass
from pathlib import Path
import re

from project_config import ProjectConfig
from strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION = 2
SUPPORTED_SCHEMA_PACK_VERSION = 2
PACK_LIFECYCLES = {"active", "deferred"}
PACK_KINDS = {"core", "domain", "extension"}
CAPABILITY_LIFECYCLES = {"available", "planned", "deprecated"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAMESPACE_PATTERN = re.compile(
    r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$"
)

EFFECT_KINDS_NAMESPACE = "occurrence.rule-effect-kind"
EFFECT_TARGET_TYPES_NAMESPACE = "occurrence.rule-effect-kind-target-type"
EFFECT_PATTERN_SCOPES_NAMESPACE = "occurrence.rule-effect-pattern-scope"
EFFECT_REPETITION_NAMESPACE = "occurrence.rule-effect-repetition-policy"
EFFECT_GLOBAL_CONFLICTS_NAMESPACE = "occurrence.rule-effect-global-incompatibility-pair"
EFFECT_TARGET_CONFLICTS_NAMESPACE = "occurrence.rule-effect-same-target-incompatibility-pair"


@dataclass(frozen=True)
class SchemaPackDependency:
    pack_id: str
    minimum_version: int


@dataclass(frozen=True)
class CapabilityConfig:
    id: str
    lifecycle: str
    label: str | None
    description: str | None


@dataclass(frozen=True)
class ControlledValueConfig:
    id: str
    label: str | None
    description: str | None
    broader_value: str | None


@dataclass(frozen=True)
class SchemaPackConfig:
    id: str
    path: Path
    schema_version: int
    pack_version: int
    lifecycle: str
    kind: str
    label: str
    description: str
    dependencies: tuple[SchemaPackDependency, ...]
    capabilities: tuple[str, ...]
    capability_definitions: dict[str, CapabilityConfig]
    controlled_values: dict[str, tuple[str, ...]]
    controlled_value_definitions: dict[str, dict[str, ControlledValueConfig]]


@dataclass(frozen=True)
class SchemaPackRegistry:
    path: Path
    schema_version: int
    packs: dict[str, SchemaPackConfig]
    selection_order: tuple[str, ...]
    declared_capabilities: tuple[str, ...]
    available_capabilities: tuple[str, ...]
    enabled_capabilities: tuple[str, ...]
    capability_providers: dict[str, tuple[str, ...]]
    capability_definitions: dict[tuple[str, str], CapabilityConfig]
    controlled_values: dict[str, tuple[str, ...]]
    controlled_value_owners: dict[tuple[str, str], str]
    controlled_value_definitions: dict[
        tuple[str, str], ControlledValueConfig
    ]

    def allowed_values(self, namespace: str) -> tuple[str, ...]:
        return self.controlled_values.get(namespace, ())

    def capability_available(self, capability: str) -> bool:
        return capability in self.available_capabilities

    def capability_enabled(self, capability: str) -> bool:
        return capability in self.enabled_capabilities

    def capability_declared(self, capability: str) -> bool:
        return capability in self.capability_providers

    def capability_definitions_for(
        self, capability: str
    ) -> tuple[tuple[str, CapabilityConfig], ...]:
        return tuple(
            (pack_id, self.capability_definitions[(pack_id, capability)])
            for pack_id in self.capability_providers.get(capability, ())
        )

    def owns_value(self, namespace: str, value: str) -> bool:
        return (namespace, value) in self.controlled_value_owners

    def owner_of(self, namespace: str, value: str) -> str | None:
        return self.controlled_value_owners.get((namespace, value))

    def definition_of(
        self, namespace: str, value: str
    ) -> ControlledValueConfig | None:
        return self.controlled_value_definitions.get((namespace, value))


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Schema-pack configuration `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Schema-pack configuration `{context}.{key}` must be a non-empty string."
        )
    return value.strip()


def require_positive_int(mapping: dict, key: str, context: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(
            f"Schema-pack configuration `{context}.{key}` must be a positive integer."
        )
    return value


def require_string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(
            f"Schema-pack configuration `{context}.{key}` must be a list of strings."
        )
    return tuple(item.strip() for item in value)


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"Schema-pack configuration `{context}` must be a lowercase kebab-case "
            f"stable ID: {value}"
        )


def validate_occurrence_semantic_declarations(
    controlled_values: dict[str, tuple[str, ...] | list[str]],
) -> None:
    effect_kinds = set(controlled_values.get(EFFECT_KINDS_NAMESPACE, ()))
    if not effect_kinds:
        return

    target_pairs = set(controlled_values.get(EFFECT_TARGET_TYPES_NAMESPACE, ()))
    recurrence_effects = {
        effect for effect in effect_kinds
        if f"{effect}-uses-recurrence-pattern" in target_pairs
    }

    scope_profiles: dict[str, set[str]] = {effect: set() for effect in recurrence_effects}
    valid_scope_values = {
        f"{effect}-{suffix}": (effect, suffix)
        for effect in recurrence_effects
        for suffix in ("uses-owning-pattern", "allows-external-pattern")
    }
    for value in controlled_values.get(EFFECT_PATTERN_SCOPES_NAMESPACE, ()):
        declaration = valid_scope_values.get(value)
        if declaration is None:
            raise ValueError(
                f"Schema-pack occurrence scope declaration `{value}` must reference a known "
                "recurrence-pattern-capable effect kind."
            )
        effect, profile = declaration
        scope_profiles[effect].add(profile)
    for effect, profiles in scope_profiles.items():
        if len(profiles) != 1:
            raise ValueError(
                f"Schema-pack effect kind `{effect}` requires exactly one recurrence-pattern scope declaration."
            )

    repetition_profiles: dict[str, set[str]] = {effect: set() for effect in effect_kinds}
    valid_repetition_values = {
        f"{effect}-uses-{policy}": (effect, policy)
        for effect in effect_kinds
        for policy in ("idempotent", "accumulating", "invalid")
    }
    for value in controlled_values.get(EFFECT_REPETITION_NAMESPACE, ()):
        declaration = valid_repetition_values.get(value)
        if declaration is None:
            raise ValueError(
                f"Schema-pack effect repetition declaration `{value}` must reference a known effect kind."
            )
        effect, policy = declaration
        repetition_profiles[effect].add(policy)
    for effect, profiles in repetition_profiles.items():
        if len(profiles) != 1:
            raise ValueError(
                f"Schema-pack effect kind `{effect}` requires exactly one repetition policy declaration."
            )

    canonical_pairs = {
        f"{left}-with-{right}"
        for index, left in enumerate(sorted(effect_kinds))
        for right in sorted(effect_kinds)[index + 1:]
    }
    global_pairs = set(controlled_values.get(EFFECT_GLOBAL_CONFLICTS_NAMESPACE, ()))
    target_pairs = set(controlled_values.get(EFFECT_TARGET_CONFLICTS_NAMESPACE, ()))
    for namespace, values in (
        (EFFECT_GLOBAL_CONFLICTS_NAMESPACE, global_pairs),
        (EFFECT_TARGET_CONFLICTS_NAMESPACE, target_pairs),
    ):
        invalid = values - canonical_pairs
        if invalid:
            raise ValueError(
                f"Schema-pack namespace `{namespace}` contains a noncanonical or unknown effect pair: "
                f"{', '.join(sorted(invalid))}."
            )
    duplicated_pairs = global_pairs & target_pairs
    if duplicated_pairs:
        raise ValueError(
            "Schema-pack effect incompatibility pairs must declare exactly one conflict scope: "
            f"{', '.join(sorted(duplicated_pairs))}."
        )


def resolve_pack_path(project: ProjectConfig, value: str, context: str) -> Path:
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise ValueError(
            f"Schema-pack configuration `{context}` must be repository-relative: "
            f"{value}"
        )
    path = (project.root / relative_path).resolve()
    if path != project.root and project.root not in path.parents:
        raise ValueError(
            f"Schema-pack configuration `{context}` escapes the repository: {value}"
        )
    if not path.is_file():
        raise ValueError(
            f"Schema-pack configuration `{context}` file does not exist: {path}"
        )
    return path


def load_pack(path: Path, expected_pack_id: str) -> SchemaPackConfig:
    data = load_yaml_file(path, "schema pack", expected_schema_version=SUPPORTED_SCHEMA_PACK_VERSION)
    pack = require_mapping(data, expected_pack_id)
    assert_allowed_keys(
        pack,
        {
            "schema_version", "pack_id", "pack_version", "lifecycle", "pack_kind",
            "label", "description", "dependencies", "capabilities", "controlled_values",
        },
        f"Schema pack `{expected_pack_id}`",
    )
    schema_version = require_positive_int(pack, "schema_version", expected_pack_id)
    if schema_version != SUPPORTED_SCHEMA_PACK_VERSION:
        raise ValueError(
            f"Unsupported schema-pack schema_version {schema_version!r} in {path}; "
            f"expected {SUPPORTED_SCHEMA_PACK_VERSION}."
        )
    pack_id = require_string(pack, "pack_id", expected_pack_id)
    validate_id(pack_id, f"{expected_pack_id}.pack_id")
    if pack_id != expected_pack_id:
        raise ValueError(
            f"Schema-pack selection `{expected_pack_id}` loads pack `{pack_id}`."
        )
    pack_version = require_positive_int(pack, "pack_version", pack_id)
    lifecycle = require_string(pack, "lifecycle", pack_id)
    if lifecycle not in PACK_LIFECYCLES:
        raise ValueError(
            f"Schema pack `{pack_id}.lifecycle` must be one of: "
            f"{', '.join(sorted(PACK_LIFECYCLES))}."
        )
    kind = require_string(pack, "pack_kind", pack_id)
    if kind not in PACK_KINDS:
        raise ValueError(
            f"Schema pack `{pack_id}.pack_kind` must be one of: "
            f"{', '.join(sorted(PACK_KINDS))}."
        )

    raw_dependencies = pack.get("dependencies")
    if not isinstance(raw_dependencies, list):
        raise ValueError(f"Schema pack `{pack_id}.dependencies` must be a list.")
    dependencies: list[SchemaPackDependency] = []
    seen_dependencies: set[str] = set()
    for index, raw_dependency in enumerate(raw_dependencies):
        context = f"{pack_id}.dependencies[{index}]"
        dependency = require_mapping(raw_dependency, context)
        assert_allowed_keys(
            dependency, {"pack_id", "minimum_version"}, f"Schema pack `{context}`"
        )
        dependency_id = require_string(dependency, "pack_id", context)
        validate_id(dependency_id, f"{context}.pack_id")
        if dependency_id == pack_id:
            raise ValueError(f"Schema pack `{pack_id}` cannot depend on itself.")
        if dependency_id in seen_dependencies:
            raise ValueError(
                f"Schema pack `{pack_id}` repeats dependency `{dependency_id}`."
            )
        seen_dependencies.add(dependency_id)
        dependencies.append(
            SchemaPackDependency(
                pack_id=dependency_id,
                minimum_version=require_positive_int(
                    dependency, "minimum_version", context
                ),
            )
        )

    raw_capabilities = pack.get("capabilities")
    if not isinstance(raw_capabilities, list) or not raw_capabilities:
        raise ValueError(f"Schema pack `{pack_id}.capabilities` cannot be empty.")
    capabilities: list[str] = []
    capability_definitions: dict[str, CapabilityConfig] = {}
    for index, raw_capability in enumerate(raw_capabilities):
        context = f"{pack_id}.capabilities[{index}]"
        if isinstance(raw_capability, str):
            capability_id = raw_capability.strip()
            lifecycle = "available"
            label = None
            description = None
        elif isinstance(raw_capability, dict):
            assert_allowed_keys(
                raw_capability,
                {"id", "lifecycle", "label", "description"},
                f"Schema pack `{context}`",
            )
            capability_id = require_string(raw_capability, "id", context)
            lifecycle = require_string(raw_capability, "lifecycle", context)
            label_value = raw_capability.get("label")
            description_value = raw_capability.get("description")
            for key, value in (
                ("label", label_value),
                ("description", description_value),
            ):
                if value is not None and (
                    not isinstance(value, str) or not value.strip()
                ):
                    raise ValueError(
                        f"Schema-pack configuration `{context}.{key}` must be a "
                        "non-empty string when present."
                    )
            label = label_value.strip() if isinstance(label_value, str) else None
            description = (
                description_value.strip()
                if isinstance(description_value, str)
                else None
            )
        else:
            raise ValueError(
                f"Schema-pack configuration `{context}` must be a stable-ID string "
                "or capability-definition mapping."
            )
        validate_id(capability_id, context)
        if lifecycle not in CAPABILITY_LIFECYCLES:
            raise ValueError(
                f"Schema pack `{context}.lifecycle` must be one of: "
                f"{', '.join(sorted(CAPABILITY_LIFECYCLES))}."
            )
        if capability_id in capability_definitions:
            raise ValueError(
                f"Schema pack `{pack_id}.capabilities` contains duplicate "
                f"`{capability_id}`."
            )
        capabilities.append(capability_id)
        capability_definitions[capability_id] = CapabilityConfig(
            id=capability_id,
            lifecycle=lifecycle,
            label=label,
            description=description,
        )

    raw_controlled = require_mapping(
        pack.get("controlled_values"), f"{pack_id}.controlled_values"
    )
    controlled_values: dict[str, tuple[str, ...]] = {}
    controlled_value_definitions: dict[
        str, dict[str, ControlledValueConfig]
    ] = {}
    for namespace, raw_values in raw_controlled.items():
        context = f"{pack_id}.controlled_values.{namespace}"
        if not isinstance(namespace, str) or not NAMESPACE_PATTERN.fullmatch(namespace):
            raise ValueError(
                f"Schema-pack controlled-value namespace must use dotted "
                f"lowercase kebab-case: {namespace}"
            )
        if not isinstance(raw_values, list) or not raw_values:
            raise ValueError(
                f"Schema-pack configuration `{context}` must be a non-empty list."
            )
        values: list[str] = []
        definitions: dict[str, ControlledValueConfig] = {}
        for index, raw_value in enumerate(raw_values):
            if isinstance(raw_value, str):
                value_id = raw_value.strip()
                label = None
                description = None
                broader_value = None
            elif isinstance(raw_value, dict):
                value_context = f"{context}[{index}]"
                assert_allowed_keys(
                    raw_value,
                    {"id", "label", "description", "broader_value"},
                    f"Schema pack `{value_context}`",
                )
                value_id = require_string(raw_value, "id", value_context)
                label = require_string(raw_value, "label", value_context)
                description_value = raw_value.get("description")
                if description_value is not None and (
                    not isinstance(description_value, str)
                    or not description_value.strip()
                ):
                    raise ValueError(
                        f"Schema-pack configuration `{value_context}.description` "
                        "must be a non-empty string when present."
                    )
                description = (
                    description_value.strip()
                    if isinstance(description_value, str)
                    else None
                )
                broader_value_raw = raw_value.get("broader_value")
                if broader_value_raw is not None and (
                    not isinstance(broader_value_raw, str)
                    or not broader_value_raw.strip()
                ):
                    raise ValueError(
                        f"Schema-pack configuration `{value_context}.broader_value` "
                        "must be a stable ID when present."
                    )
                broader_value = (
                    broader_value_raw.strip()
                    if isinstance(broader_value_raw, str)
                    else None
                )
            else:
                raise ValueError(
                    f"Schema-pack configuration `{context}` must contain stable-ID "
                    "strings or value-definition mappings."
                )
            validate_id(value_id, context)
            if broader_value:
                validate_id(broader_value, f"{context}.broader_value")
                if broader_value == value_id:
                    raise ValueError(
                        f"Schema-pack controlled value `{namespace}:{value_id}` "
                        "cannot be broader than itself."
                    )
            values.append(value_id)
            definitions[value_id] = ControlledValueConfig(
                id=value_id,
                label=label,
                description=description,
                broader_value=broader_value,
            )
        if len(set(values)) != len(values):
            raise ValueError(
                f"Schema-pack configuration `{context}` contains duplicates."
            )
        controlled_values[namespace] = tuple(values)
        controlled_value_definitions[namespace] = definitions

    return SchemaPackConfig(
        id=pack_id,
        path=path,
        schema_version=schema_version,
        pack_version=pack_version,
        lifecycle=lifecycle,
        kind=kind,
        label=require_string(pack, "label", pack_id),
        description=require_string(pack, "description", pack_id),
        dependencies=tuple(dependencies),
        capabilities=tuple(capabilities),
        capability_definitions=capability_definitions,
        controlled_values=controlled_values,
        controlled_value_definitions=controlled_value_definitions,
    )


def load_schema_pack_registry(project: ProjectConfig) -> SchemaPackRegistry:
    path = project.schema_packs_registry
    data = load_yaml_file(path, "schema-pack registry", expected_schema_version=SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION)
    registry = require_mapping(data, "root")
    assert_allowed_keys(
        registry,
        {"schema_version", "selected_packs", "capability_activation"},
        "Schema-pack registry root",
    )
    schema_version = require_positive_int(registry, "schema_version", "root")
    if schema_version != SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION:
        raise ValueError(
            f"Unsupported schema-pack registry version {schema_version!r}; expected "
            f"{SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION}."
        )
    raw_selections = registry.get("selected_packs")
    if not isinstance(raw_selections, list) or not raw_selections:
        raise ValueError(
            "Schema-pack registry `selected_packs` must be a non-empty list."
        )

    packs: dict[str, SchemaPackConfig] = {}
    selection_order: list[str] = []
    for index, raw_selection in enumerate(raw_selections):
        context = f"selected_packs[{index}]"
        selection = require_mapping(raw_selection, context)
        assert_allowed_keys(
            selection, {"pack_id", "path"}, f"Schema-pack registry `{context}`"
        )
        pack_id = require_string(selection, "pack_id", context)
        validate_id(pack_id, f"{context}.pack_id")
        if pack_id in packs:
            raise ValueError(f"Schema-pack registry repeats pack `{pack_id}`.")
        pack_path = resolve_pack_path(
            project,
            require_string(selection, "path", context),
            f"{context}.path",
        )
        packs[pack_id] = load_pack(pack_path, pack_id)
        selection_order.append(pack_id)

    selected_before: set[str] = set()
    for pack_id in selection_order:
        pack = packs[pack_id]
        for dependency in pack.dependencies:
            if dependency.pack_id not in packs:
                raise ValueError(
                    f"Schema pack `{pack_id}` requires unselected pack "
                    f"`{dependency.pack_id}`."
                )
            if dependency.pack_id not in selected_before:
                raise ValueError(
                    f"Schema pack `{pack_id}` must be selected after dependency "
                    f"`{dependency.pack_id}`."
                )
            installed = packs[dependency.pack_id]
            if installed.pack_version < dependency.minimum_version:
                raise ValueError(
                    f"Schema pack `{pack_id}` requires `{dependency.pack_id}` version "
                    f"{dependency.minimum_version} or newer; selected version is "
                    f"{installed.pack_version}."
                )
        selected_before.add(pack_id)

    declared_capabilities: list[str] = []
    available_capabilities: list[str] = []
    capability_providers: dict[str, list[str]] = {}
    capability_definitions: dict[tuple[str, str], CapabilityConfig] = {}
    for pack_id in selection_order:
        for capability in packs[pack_id].capabilities:
            providers = capability_providers.setdefault(capability, [])
            providers.append(pack_id)
            if capability not in declared_capabilities:
                declared_capabilities.append(capability)
            definition = packs[pack_id].capability_definitions[capability]
            capability_definitions[(pack_id, capability)] = definition
            if (
                definition.lifecycle in {"available", "deprecated"}
                and capability not in available_capabilities
            ):
                available_capabilities.append(capability)

    activation = require_mapping(
        registry.get("capability_activation"), "capability_activation"
    )
    assert_allowed_keys(
        activation,
        {"default", "enabled"},
        "Schema-pack registry `capability_activation`",
    )
    activation_default = require_string(
        activation, "default", "capability_activation"
    )
    if activation_default != "disabled":
        raise ValueError(
            "Schema-pack registry `capability_activation.default` must be "
            "`disabled` so features remain opt-in."
        )
    enabled_capabilities = require_string_list(
        activation, "enabled", "capability_activation"
    )
    if len(set(enabled_capabilities)) != len(enabled_capabilities):
        raise ValueError(
            "Schema-pack registry `capability_activation.enabled` contains "
            "duplicates."
        )
    for capability in enabled_capabilities:
        validate_id(capability, "capability_activation.enabled")
    unavailable_enabled = set(enabled_capabilities) - set(available_capabilities)
    if unavailable_enabled:
        raise ValueError(
            "Schema-pack registry enables capabilities that are not available or "
            "deprecated in selected packs: "
            f"{', '.join(sorted(unavailable_enabled))}."
        )

    controlled: dict[str, list[str]] = {}
    owners: dict[tuple[str, str], str] = {}
    definitions: dict[tuple[str, str], ControlledValueConfig] = {}
    for pack_id in selection_order:
        for namespace, values in packs[pack_id].controlled_values.items():
            target = controlled.setdefault(namespace, [])
            for value in values:
                key = (namespace, value)
                if key in owners:
                    raise ValueError(
                        f"Schema-pack controlled value `{namespace}:{value}` is "
                        f"provided by both `{owners[key]}` and `{pack_id}`."
                    )
                owners[key] = pack_id
                target.append(value)
                definitions[key] = packs[pack_id].controlled_value_definitions[
                    namespace
                ][value]

    for (namespace, value), definition in definitions.items():
        broader = definition.broader_value
        if broader and (namespace, broader) not in owners:
            raise ValueError(
                f"Schema-pack controlled value `{namespace}:{value}` references "
                f"unknown broader value `{broader}`."
            )
    complete_values: set[tuple[str, str]] = set()

    def visit_value(key: tuple[str, str], active: set[tuple[str, str]]) -> None:
        if key in active:
            raise ValueError(
                f"Schema-pack controlled-value hierarchy contains a cycle at "
                f"`{key[0]}:{key[1]}`."
            )
        if key in complete_values:
            return
        active.add(key)
        broader = definitions[key].broader_value
        if broader:
            visit_value((key[0], broader), active)
        active.remove(key)
        complete_values.add(key)

    for key in definitions:
        visit_value(key, set())

    validate_occurrence_semantic_declarations(controlled)

    return SchemaPackRegistry(
        path=path,
        schema_version=schema_version,
        packs=packs,
        selection_order=tuple(selection_order),
        declared_capabilities=tuple(declared_capabilities),
        available_capabilities=tuple(available_capabilities),
        enabled_capabilities=enabled_capabilities,
        capability_providers={
            capability: tuple(providers)
            for capability, providers in capability_providers.items()
        },
        capability_definitions=capability_definitions,
        controlled_values={
            namespace: tuple(values) for namespace, values in controlled.items()
        },
        controlled_value_owners=owners,
        controlled_value_definitions=definitions,
    )
