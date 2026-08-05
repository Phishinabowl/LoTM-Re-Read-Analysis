from dataclasses import dataclass
from pathlib import Path
import re

from .project_config import ProjectConfig
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION = 2
SUPPORTED_SCHEMA_PACK_VERSION = 4
PACK_LIFECYCLES = {"active", "deferred"}
PACK_KINDS = {"core", "domain", "extension"}
CAPABILITY_LIFECYCLES = {"available", "planned", "deprecated"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")

LEGACY_COMPOUND_SEMANTIC_NAMESPACES = {
    "occurrence.transition-kind-profile",
    "occurrence.outcome-incompatibility-pair",
    "occurrence.rule-effect-kind-target-type",
    "occurrence.rule-kind-effect-kind",
    "occurrence.rule-effect-pattern-scope",
    "occurrence.rule-effect-repetition-policy",
    "occurrence.rule-effect-global-incompatibility-pair",
    "occurrence.rule-effect-same-target-incompatibility-pair",
    "state.change-kind-profile",
}
EFFECT_REPETITION_POLICIES = {"idempotent", "accumulating", "invalid"}
EFFECT_PATTERN_SCOPES = {"owning-pattern", "external-pattern"}
EFFECT_INCOMPATIBILITY_SCOPES = {"global", "same-target"}
EFFECT_TARGET_TYPE_NAMESPACE = "occurrence.rule-effect-target-type"
STATE_DIMENSION_REQUIREMENTS = {"required", "optional", "forbidden"}


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
class TransitionProfileDeclaration:
    transition_kind: str
    transition_profile: str


@dataclass(frozen=True)
class OutcomeIncompatibilityDeclaration:
    members: tuple[str, str]


@dataclass(frozen=True)
class EffectTargetCompatibilityDeclaration:
    effect_kind: str
    target_type: str


@dataclass(frozen=True)
class RuleEffectCompatibilityDeclaration:
    rule_kind: str
    effect_kind: str


@dataclass(frozen=True)
class EffectPolicyDeclaration:
    effect_kind: str
    repetition_policy: str
    recurrence_pattern_scope: str | None


@dataclass(frozen=True)
class EffectIncompatibilityDeclaration:
    members: tuple[str, str]
    scope: str


@dataclass(frozen=True)
class StateChangeProfileDeclaration:
    change_kind: str
    change_profile: str


@dataclass(frozen=True)
class StateProfileDeclaration:
    profile_id: str
    availability: str
    completeness: str
    attitude: str
    capability: str


@dataclass(frozen=True)
class StateKindProfileDeclaration:
    state_kind: str
    profile_id: str


@dataclass(frozen=True)
class SemanticDeclarations:
    transition_profiles: tuple[TransitionProfileDeclaration, ...] = ()
    outcome_incompatibilities: tuple[OutcomeIncompatibilityDeclaration, ...] = ()
    effect_target_compatibilities: tuple[EffectTargetCompatibilityDeclaration, ...] = ()
    rule_effect_compatibilities: tuple[RuleEffectCompatibilityDeclaration, ...] = ()
    effect_policies: tuple[EffectPolicyDeclaration, ...] = ()
    effect_incompatibilities: tuple[EffectIncompatibilityDeclaration, ...] = ()
    state_change_profiles: tuple[StateChangeProfileDeclaration, ...] = ()
    state_profiles: tuple[StateProfileDeclaration, ...] = ()
    state_kind_profiles: tuple[StateKindProfileDeclaration, ...] = ()


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
    semantic_declarations: SemanticDeclarations


@dataclass(frozen=True)
# TODO (OWNER): Expose this composition through the planned EffectiveProjectSchema service.
#   Consumers should not reconstruct pack, capability, and vocabulary state from these maps.
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
    controlled_value_definitions: dict[tuple[str, str], ControlledValueConfig]
    transition_profiles: dict[str, str]
    outcome_incompatibilities: frozenset[tuple[str, str]]
    effect_target_compatibilities: frozenset[tuple[str, str]]
    rule_effect_compatibilities: frozenset[tuple[str, str]]
    effect_policies: dict[str, EffectPolicyDeclaration]
    effect_incompatibilities: dict[tuple[str, str], str]
    state_change_profiles: dict[str, str]
    state_profiles: dict[str, StateProfileDeclaration]
    state_kind_profiles: dict[str, str]
    semantic_declaration_owners: dict[tuple[str, ...], str]

    def allowed_values(self, namespace: str) -> tuple[str, ...]:
        return self.controlled_values.get(namespace, ())

    def capability_available(self, capability: str) -> bool:
        return capability in self.available_capabilities

    def capability_enabled(self, capability: str) -> bool:
        return capability in self.enabled_capabilities

    def capability_declared(self, capability: str) -> bool:
        return capability in self.capability_providers

    def capability_definitions_for(self, capability: str) -> tuple[tuple[str, CapabilityConfig], ...]:
        return tuple(
            (pack_id, self.capability_definitions[(pack_id, capability)])
            for pack_id in self.capability_providers.get(capability, ())
        )

    def owns_value(self, namespace: str, value: str) -> bool:
        return (namespace, value) in self.controlled_value_owners

    def owner_of(self, namespace: str, value: str) -> str | None:
        return self.controlled_value_owners.get((namespace, value))

    def definition_of(self, namespace: str, value: str) -> ControlledValueConfig | None:
        return self.controlled_value_definitions.get((namespace, value))


def require_mapping(value, context: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"Schema-pack configuration `{context}` must be a mapping.")
    return value


def require_string(mapping: dict, key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be a non-empty string.")
    return value.strip()


def require_positive_int(mapping: dict, key: str, context: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be a positive integer.")
    return value


def require_string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be a list of strings.")
    return tuple(item.strip() for item in value)


def validate_id(value: str, context: str) -> None:
    if not STABLE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Schema-pack configuration `{context}` must be a lowercase kebab-case stable ID: {value}")


def _optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be a non-empty string when present.")
    return value.strip()


def _declaration_rows(mapping: dict, key: str, context: str) -> list:
    value = mapping.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be a list.")
    return value


def _pair_members(mapping: dict, context: str) -> tuple[str, str]:
    members = require_string_list(mapping, "members", context)
    if len(members) != 2:
        raise ValueError(f"Schema-pack configuration `{context}.members` must contain exactly two stable IDs.")
    for member in members:
        validate_id(member, f"{context}.members")
    if members[0] == members[1]:
        raise ValueError(f"Schema-pack configuration `{context}.members` must contain distinct stable IDs.")
    return tuple(sorted(members))


def parse_semantic_declarations(pack: dict, pack_id: str) -> SemanticDeclarations:
    raw = pack.get("semantic_declarations", {})
    declarations = require_mapping(raw, f"{pack_id}.semantic_declarations")
    assert_allowed_keys(declarations, {"occurrence", "state"}, f"Schema pack `{pack_id}.semantic_declarations`")
    occurrence = require_mapping(declarations.get("occurrence", {}), f"{pack_id}.semantic_declarations.occurrence")
    assert_allowed_keys(
        occurrence,
        {
            "transition_profiles",
            "outcome_incompatibilities",
            "effect_target_compatibilities",
            "rule_effect_compatibilities",
            "effect_policies",
            "effect_incompatibilities",
        },
        f"Schema pack `{pack_id}.semantic_declarations.occurrence`",
    )
    state = require_mapping(declarations.get("state", {}), f"{pack_id}.semantic_declarations.state")
    assert_allowed_keys(
        state,
        {"change_profiles", "profiles", "kind_profiles"},
        f"Schema pack `{pack_id}.semantic_declarations.state`",
    )

    transition_profiles = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "transition_profiles", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.transition_profiles[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"transition_kind", "transition_profile"}, f"Schema pack `{context}`")
        kind = require_string(row, "transition_kind", context)
        profile = require_string(row, "transition_profile", context)
        validate_id(kind, f"{context}.transition_kind")
        validate_id(profile, f"{context}.transition_profile")
        transition_profiles.append(TransitionProfileDeclaration(kind, profile))

    outcome_incompatibilities = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "outcome_incompatibilities", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.outcome_incompatibilities[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"members"}, f"Schema pack `{context}`")
        outcome_incompatibilities.append(OutcomeIncompatibilityDeclaration(_pair_members(row, context)))

    target_compatibilities = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "effect_target_compatibilities", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.effect_target_compatibilities[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"effect_kind", "target_type"}, f"Schema pack `{context}`")
        effect_kind = require_string(row, "effect_kind", context)
        target_type = require_string(row, "target_type", context)
        validate_id(effect_kind, f"{context}.effect_kind")
        validate_id(target_type, f"{context}.target_type")
        target_compatibilities.append(EffectTargetCompatibilityDeclaration(effect_kind, target_type))

    rule_compatibilities = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "rule_effect_compatibilities", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.rule_effect_compatibilities[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"rule_kind", "effect_kind"}, f"Schema pack `{context}`")
        rule_kind = require_string(row, "rule_kind", context)
        effect_kind = require_string(row, "effect_kind", context)
        validate_id(rule_kind, f"{context}.rule_kind")
        validate_id(effect_kind, f"{context}.effect_kind")
        rule_compatibilities.append(RuleEffectCompatibilityDeclaration(rule_kind, effect_kind))

    effect_policies = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "effect_policies", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.effect_policies[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(
            row,
            {"effect_kind", "repetition_policy", "recurrence_pattern_scope"},
            f"Schema pack `{context}`",
        )
        effect_kind = require_string(row, "effect_kind", context)
        repetition_policy = require_string(row, "repetition_policy", context)
        recurrence_scope = _optional_string(row, "recurrence_pattern_scope", context)
        validate_id(effect_kind, f"{context}.effect_kind")
        if repetition_policy not in EFFECT_REPETITION_POLICIES:
            raise ValueError(f"Schema-pack configuration `{context}.repetition_policy` is unsupported.")
        if recurrence_scope is not None and recurrence_scope not in EFFECT_PATTERN_SCOPES:
            raise ValueError(f"Schema-pack configuration `{context}.recurrence_pattern_scope` is unsupported.")
        effect_policies.append(EffectPolicyDeclaration(effect_kind, repetition_policy, recurrence_scope))

    effect_incompatibilities = []
    for index, raw_row in enumerate(_declaration_rows(occurrence, "effect_incompatibilities", pack_id)):
        context = f"{pack_id}.semantic_declarations.occurrence.effect_incompatibilities[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"members", "scope"}, f"Schema pack `{context}`")
        scope = require_string(row, "scope", context)
        if scope not in EFFECT_INCOMPATIBILITY_SCOPES:
            raise ValueError(f"Schema-pack configuration `{context}.scope` is unsupported.")
        effect_incompatibilities.append(EffectIncompatibilityDeclaration(_pair_members(row, context), scope))

    change_profiles = []
    for index, raw_row in enumerate(_declaration_rows(state, "change_profiles", pack_id)):
        context = f"{pack_id}.semantic_declarations.state.change_profiles[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"change_kind", "change_profile"}, f"Schema pack `{context}`")
        change_kind = require_string(row, "change_kind", context)
        change_profile = require_string(row, "change_profile", context)
        validate_id(change_kind, f"{context}.change_kind")
        validate_id(change_profile, f"{context}.change_profile")
        change_profiles.append(StateChangeProfileDeclaration(change_kind, change_profile))

    state_profiles = []
    for index, raw_row in enumerate(_declaration_rows(state, "profiles", pack_id)):
        context = f"{pack_id}.semantic_declarations.state.profiles[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(
            row,
            {"profile_id", "availability", "completeness", "attitude", "capability"},
            f"Schema pack `{context}`",
        )
        profile_id = require_string(row, "profile_id", context)
        validate_id(profile_id, f"{context}.profile_id")
        requirements = tuple(
            require_string(row, key, context) for key in ("availability", "completeness", "attitude", "capability")
        )
        if any(requirement not in STATE_DIMENSION_REQUIREMENTS for requirement in requirements):
            raise ValueError(f"Schema-pack configuration `{context}` has an unsupported dimension requirement.")
        if requirements[0] != "required":
            raise ValueError(f"Schema-pack configuration `{context}.availability` must be `required`.")
        if all(requirement == "forbidden" for requirement in requirements):
            raise ValueError(f"Schema-pack configuration `{context}` must use at least one state dimension.")
        state_profiles.append(StateProfileDeclaration(profile_id, *requirements))

    state_kind_profiles = []
    for index, raw_row in enumerate(_declaration_rows(state, "kind_profiles", pack_id)):
        context = f"{pack_id}.semantic_declarations.state.kind_profiles[{index}]"
        row = require_mapping(raw_row, context)
        assert_allowed_keys(row, {"state_kind", "profile_id"}, f"Schema pack `{context}`")
        state_kind = require_string(row, "state_kind", context)
        profile_id = require_string(row, "profile_id", context)
        validate_id(state_kind, f"{context}.state_kind")
        validate_id(profile_id, f"{context}.profile_id")
        state_kind_profiles.append(StateKindProfileDeclaration(state_kind, profile_id))

    return SemanticDeclarations(
        tuple(transition_profiles),
        tuple(outcome_incompatibilities),
        tuple(target_compatibilities),
        tuple(rule_compatibilities),
        tuple(effect_policies),
        tuple(effect_incompatibilities),
        tuple(change_profiles),
        tuple(state_profiles),
        tuple(state_kind_profiles),
    )


def resolve_pack_path(project: ProjectConfig, value: str, context: str) -> Path:
    relative_path = Path(value)
    if relative_path.is_absolute():
        raise ValueError(f"Schema-pack configuration `{context}` must be repository-relative: {value}")
    path = (project.root / relative_path).resolve()
    if path != project.root and project.root not in path.parents:
        raise ValueError(f"Schema-pack configuration `{context}` escapes the repository: {value}")
    if not path.is_file():
        raise ValueError(f"Schema-pack configuration `{context}` file does not exist: {path}")
    return path


def compose_semantic_declarations(
    packs: dict[str, SchemaPackConfig],
    selection_order: list[str],
    controlled_values: dict[str, list[str]],
) -> tuple[
    dict[str, str],
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str]],
    frozenset[tuple[str, str]],
    dict[str, EffectPolicyDeclaration],
    dict[tuple[str, str], str],
    dict[str, str],
    dict[str, StateProfileDeclaration],
    dict[str, str],
    dict[tuple[str, ...], str],
]:
    values = {namespace: set(items) for namespace, items in controlled_values.items()}
    owners: dict[tuple[str, ...], str] = {}
    transition_profiles: dict[str, str] = {}
    outcome_incompatibilities: set[tuple[str, str]] = set()
    target_compatibilities: set[tuple[str, str]] = set()
    rule_compatibilities: set[tuple[str, str]] = set()
    effect_policies: dict[str, EffectPolicyDeclaration] = {}
    effect_incompatibilities: dict[tuple[str, str], str] = {}
    state_change_profiles: dict[str, str] = {}
    state_profiles: dict[str, StateProfileDeclaration] = {}
    state_kind_profiles: dict[str, str] = {}

    def require_atom(namespace: str, value: str, context: str) -> None:
        if value not in values.get(namespace, set()):
            raise ValueError(f"Schema-pack semantic declaration `{context}` references unknown `{namespace}:{value}`.")

    def register(key: tuple[str, ...], pack_id: str) -> None:
        if key in owners:
            raise ValueError(
                f"Schema-pack semantic declaration `{'|'.join(key)}` is provided by both "
                f"`{owners[key]}` and `{pack_id}`."
            )
        owners[key] = pack_id

    for pack_id in selection_order:
        declarations = packs[pack_id].semantic_declarations
        for declaration in declarations.transition_profiles:
            context = f"{pack_id}.transition_profiles.{declaration.transition_kind}"
            require_atom("occurrence.transition-kind", declaration.transition_kind, context)
            require_atom("occurrence.transition-profile", declaration.transition_profile, context)
            key = ("transition-profile", declaration.transition_kind)
            register(key, pack_id)
            transition_profiles[declaration.transition_kind] = declaration.transition_profile
        for declaration in declarations.outcome_incompatibilities:
            for member in declaration.members:
                require_atom("occurrence.outcome-kind", member, f"{pack_id}.outcome_incompatibilities")
            key = ("outcome-incompatibility", *declaration.members)
            register(key, pack_id)
            outcome_incompatibilities.add(declaration.members)
        for declaration in declarations.effect_target_compatibilities:
            context = f"{pack_id}.effect_target_compatibilities"
            require_atom("occurrence.rule-effect-kind", declaration.effect_kind, context)
            require_atom(EFFECT_TARGET_TYPE_NAMESPACE, declaration.target_type, context)
            pair = (declaration.effect_kind, declaration.target_type)
            register(("effect-target-compatibility", *pair), pack_id)
            target_compatibilities.add(pair)
        for declaration in declarations.rule_effect_compatibilities:
            context = f"{pack_id}.rule_effect_compatibilities"
            require_atom("occurrence.rule-kind", declaration.rule_kind, context)
            require_atom("occurrence.rule-effect-kind", declaration.effect_kind, context)
            pair = (declaration.rule_kind, declaration.effect_kind)
            register(("rule-effect-compatibility", *pair), pack_id)
            rule_compatibilities.add(pair)
        for declaration in declarations.effect_policies:
            context = f"{pack_id}.effect_policies.{declaration.effect_kind}"
            require_atom("occurrence.rule-effect-kind", declaration.effect_kind, context)
            register(("effect-policy", declaration.effect_kind), pack_id)
            effect_policies[declaration.effect_kind] = declaration
        for declaration in declarations.effect_incompatibilities:
            for member in declaration.members:
                require_atom("occurrence.rule-effect-kind", member, f"{pack_id}.effect_incompatibilities")
            register(("effect-incompatibility", *declaration.members), pack_id)
            effect_incompatibilities[declaration.members] = declaration.scope
        for declaration in declarations.state_change_profiles:
            context = f"{pack_id}.change_profiles.{declaration.change_kind}"
            require_atom("state.change-kind", declaration.change_kind, context)
            require_atom("state.change-profile", declaration.change_profile, context)
            register(("state-change-profile", declaration.change_kind), pack_id)
            state_change_profiles[declaration.change_kind] = declaration.change_profile
        for declaration in declarations.state_profiles:
            register(("state-profile", declaration.profile_id), pack_id)
            state_profiles[declaration.profile_id] = declaration
        for declaration in declarations.state_kind_profiles:
            context = f"{pack_id}.kind_profiles.{declaration.state_kind}"
            require_atom("state.state-kind", declaration.state_kind, context)
            register(("state-kind-profile", declaration.state_kind), pack_id)
            state_kind_profiles[declaration.state_kind] = declaration.profile_id

    transition_kinds = values.get("occurrence.transition-kind", set())
    if set(transition_profiles) != transition_kinds:
        missing = sorted(transition_kinds - set(transition_profiles))
        raise ValueError(f"Schema-pack transition kinds require exactly one typed profile: {', '.join(missing)}.")
    change_kinds = values.get("state.change-kind", set())
    if set(state_change_profiles) != change_kinds:
        missing = sorted(change_kinds - set(state_change_profiles))
        raise ValueError(f"Schema-pack state change kinds require exactly one typed profile: {', '.join(missing)}.")
    state_kinds = values.get("state.state-kind", set())
    if set(state_kind_profiles) != state_kinds:
        missing = sorted(state_kinds - set(state_kind_profiles))
        raise ValueError(f"Schema-pack state kinds require exactly one typed profile: {', '.join(missing)}.")
    unknown_profiles = sorted(set(state_kind_profiles.values()) - set(state_profiles))
    if unknown_profiles:
        raise ValueError(f"Schema-pack state-kind mappings reference unknown profiles: {', '.join(unknown_profiles)}.")
    effect_kinds = values.get("occurrence.rule-effect-kind", set())
    if set(effect_policies) != effect_kinds:
        missing = sorted(effect_kinds - set(effect_policies))
        raise ValueError(f"Schema-pack effect kinds require exactly one typed policy: {', '.join(missing)}.")
    effects_with_targets = {effect_kind for effect_kind, _ in target_compatibilities}
    missing_targets = sorted(effect_kinds - effects_with_targets)
    if missing_targets:
        raise ValueError(
            f"Schema-pack effect kinds require a typed target compatibility: {', '.join(missing_targets)}."
        )
    effects_with_rules = {effect_kind for _, effect_kind in rule_compatibilities}
    missing_rules = sorted(effect_kinds - effects_with_rules)
    if missing_rules:
        raise ValueError(f"Schema-pack effect kinds require a typed rule compatibility: {', '.join(missing_rules)}.")
    for effect_kind, policy in effect_policies.items():
        targets_recurrence = (effect_kind, "recurrence-pattern") in target_compatibilities
        if targets_recurrence != (policy.recurrence_pattern_scope is not None):
            requirement = "requires" if targets_recurrence else "must not declare"
            raise ValueError(f"Schema-pack effect kind `{effect_kind}` {requirement} a recurrence-pattern scope.")

    return (
        transition_profiles,
        frozenset(outcome_incompatibilities),
        frozenset(target_compatibilities),
        frozenset(rule_compatibilities),
        effect_policies,
        effect_incompatibilities,
        state_change_profiles,
        state_profiles,
        state_kind_profiles,
        owners,
    )


def load_pack(path: Path, expected_pack_id: str) -> SchemaPackConfig:
    data = load_yaml_file(path, "schema pack", expected_schema_version=SUPPORTED_SCHEMA_PACK_VERSION)
    pack = require_mapping(data, expected_pack_id)
    assert_allowed_keys(
        pack,
        {
            "schema_version",
            "pack_id",
            "pack_version",
            "lifecycle",
            "pack_kind",
            "label",
            "description",
            "dependencies",
            "capabilities",
            "controlled_values",
            "semantic_declarations",
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
        raise ValueError(f"Schema-pack selection `{expected_pack_id}` loads pack `{pack_id}`.")
    pack_version = require_positive_int(pack, "pack_version", pack_id)
    lifecycle = require_string(pack, "lifecycle", pack_id)
    if lifecycle not in PACK_LIFECYCLES:
        raise ValueError(f"Schema pack `{pack_id}.lifecycle` must be one of: {', '.join(sorted(PACK_LIFECYCLES))}.")
    kind = require_string(pack, "pack_kind", pack_id)
    if kind not in PACK_KINDS:
        raise ValueError(f"Schema pack `{pack_id}.pack_kind` must be one of: {', '.join(sorted(PACK_KINDS))}.")

    raw_dependencies = pack.get("dependencies")
    if not isinstance(raw_dependencies, list):
        raise ValueError(f"Schema pack `{pack_id}.dependencies` must be a list.")
    dependencies: list[SchemaPackDependency] = []
    seen_dependencies: set[str] = set()
    for index, raw_dependency in enumerate(raw_dependencies):
        context = f"{pack_id}.dependencies[{index}]"
        dependency = require_mapping(raw_dependency, context)
        assert_allowed_keys(dependency, {"pack_id", "minimum_version"}, f"Schema pack `{context}`")
        dependency_id = require_string(dependency, "pack_id", context)
        validate_id(dependency_id, f"{context}.pack_id")
        if dependency_id == pack_id:
            raise ValueError(f"Schema pack `{pack_id}` cannot depend on itself.")
        if dependency_id in seen_dependencies:
            raise ValueError(f"Schema pack `{pack_id}` repeats dependency `{dependency_id}`.")
        seen_dependencies.add(dependency_id)
        dependencies.append(
            SchemaPackDependency(
                pack_id=dependency_id,
                minimum_version=require_positive_int(dependency, "minimum_version", context),
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
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    raise ValueError(
                        f"Schema-pack configuration `{context}.{key}` must be a non-empty string when present."
                    )
            label = label_value.strip() if isinstance(label_value, str) else None
            description = description_value.strip() if isinstance(description_value, str) else None
        else:
            raise ValueError(
                f"Schema-pack configuration `{context}` must be a stable-ID string or capability-definition mapping."
            )
        validate_id(capability_id, context)
        if lifecycle not in CAPABILITY_LIFECYCLES:
            raise ValueError(
                f"Schema pack `{context}.lifecycle` must be one of: {', '.join(sorted(CAPABILITY_LIFECYCLES))}."
            )
        if capability_id in capability_definitions:
            raise ValueError(f"Schema pack `{pack_id}.capabilities` contains duplicate `{capability_id}`.")
        capabilities.append(capability_id)
        capability_definitions[capability_id] = CapabilityConfig(
            id=capability_id,
            lifecycle=lifecycle,
            label=label,
            description=description,
        )

    raw_controlled = require_mapping(pack.get("controlled_values"), f"{pack_id}.controlled_values")
    controlled_values: dict[str, tuple[str, ...]] = {}
    controlled_value_definitions: dict[str, dict[str, ControlledValueConfig]] = {}
    for namespace, raw_values in raw_controlled.items():
        context = f"{pack_id}.controlled_values.{namespace}"
        if not isinstance(namespace, str) or not NAMESPACE_PATTERN.fullmatch(namespace):
            raise ValueError(
                f"Schema-pack controlled-value namespace must use dotted lowercase kebab-case: {namespace}"
            )
        if not isinstance(raw_values, list) or not raw_values:
            raise ValueError(f"Schema-pack configuration `{context}` must be a non-empty list.")
        if namespace in LEGACY_COMPOUND_SEMANTIC_NAMESPACES:
            raise ValueError(
                f"Schema-pack controlled-value namespace `{namespace}` was replaced by typed semantic declarations."
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
                    not isinstance(description_value, str) or not description_value.strip()
                ):
                    raise ValueError(
                        f"Schema-pack configuration `{value_context}.description` "
                        "must be a non-empty string when present."
                    )
                description = description_value.strip() if isinstance(description_value, str) else None
                broader_value_raw = raw_value.get("broader_value")
                if broader_value_raw is not None and (
                    not isinstance(broader_value_raw, str) or not broader_value_raw.strip()
                ):
                    raise ValueError(
                        f"Schema-pack configuration `{value_context}.broader_value` must be a stable ID when present."
                    )
                broader_value = broader_value_raw.strip() if isinstance(broader_value_raw, str) else None
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
                        f"Schema-pack controlled value `{namespace}:{value_id}` cannot be broader than itself."
                    )
            values.append(value_id)
            definitions[value_id] = ControlledValueConfig(
                id=value_id,
                label=label,
                description=description,
                broader_value=broader_value,
            )
        if len(set(values)) != len(values):
            raise ValueError(f"Schema-pack configuration `{context}` contains duplicates.")
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
        semantic_declarations=parse_semantic_declarations(pack, pack_id),
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
        raise ValueError("Schema-pack registry `selected_packs` must be a non-empty list.")

    packs: dict[str, SchemaPackConfig] = {}
    selection_order: list[str] = []
    for index, raw_selection in enumerate(raw_selections):
        context = f"selected_packs[{index}]"
        selection = require_mapping(raw_selection, context)
        assert_allowed_keys(selection, {"pack_id", "path"}, f"Schema-pack registry `{context}`")
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
                raise ValueError(f"Schema pack `{pack_id}` requires unselected pack `{dependency.pack_id}`.")
            if dependency.pack_id not in selected_before:
                raise ValueError(f"Schema pack `{pack_id}` must be selected after dependency `{dependency.pack_id}`.")
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
            if definition.lifecycle in {"available", "deprecated"} and capability not in available_capabilities:
                available_capabilities.append(capability)

    activation = require_mapping(registry.get("capability_activation"), "capability_activation")
    assert_allowed_keys(
        activation,
        {"default", "enabled"},
        "Schema-pack registry `capability_activation`",
    )
    activation_default = require_string(activation, "default", "capability_activation")
    if activation_default != "disabled":
        raise ValueError(
            "Schema-pack registry `capability_activation.default` must be `disabled` so features remain opt-in."
        )
    enabled_capabilities = require_string_list(activation, "enabled", "capability_activation")
    if len(set(enabled_capabilities)) != len(enabled_capabilities):
        raise ValueError("Schema-pack registry `capability_activation.enabled` contains duplicates.")
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
                definitions[key] = packs[pack_id].controlled_value_definitions[namespace][value]

    for (namespace, value), definition in definitions.items():
        broader = definition.broader_value
        if broader and (namespace, broader) not in owners:
            raise ValueError(
                f"Schema-pack controlled value `{namespace}:{value}` references unknown broader value `{broader}`."
            )
    complete_values: set[tuple[str, str]] = set()

    def visit_value(key: tuple[str, str], active: set[tuple[str, str]]) -> None:
        if key in active:
            raise ValueError(f"Schema-pack controlled-value hierarchy contains a cycle at `{key[0]}:{key[1]}`.")
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

    (
        transition_profiles,
        outcome_incompatibilities,
        effect_target_compatibilities,
        rule_effect_compatibilities,
        effect_policies,
        effect_incompatibilities,
        state_change_profiles,
        state_profiles,
        state_kind_profiles,
        semantic_declaration_owners,
    ) = compose_semantic_declarations(packs, selection_order, controlled)

    return SchemaPackRegistry(
        path=path,
        schema_version=schema_version,
        packs=packs,
        selection_order=tuple(selection_order),
        declared_capabilities=tuple(declared_capabilities),
        available_capabilities=tuple(available_capabilities),
        enabled_capabilities=enabled_capabilities,
        capability_providers={capability: tuple(providers) for capability, providers in capability_providers.items()},
        capability_definitions=capability_definitions,
        controlled_values={namespace: tuple(values) for namespace, values in controlled.items()},
        controlled_value_owners=owners,
        controlled_value_definitions=definitions,
        transition_profiles=transition_profiles,
        outcome_incompatibilities=outcome_incompatibilities,
        effect_target_compatibilities=effect_target_compatibilities,
        rule_effect_compatibilities=rule_effect_compatibilities,
        effect_policies=effect_policies,
        effect_incompatibilities=effect_incompatibilities,
        state_change_profiles=state_change_profiles,
        state_profiles=state_profiles,
        state_kind_profiles=state_kind_profiles,
        semantic_declaration_owners=semantic_declaration_owners,
    )
