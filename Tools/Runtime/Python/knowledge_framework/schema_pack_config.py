from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlparse

from .project_config import ProjectConfig
from .strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_SCHEMA_PACK_REGISTRY_VERSION = 2
SUPPORTED_SCHEMA_PACK_VERSIONS = (4, 5)
CURRENT_SCHEMA_PACK_VERSION = 5
PACK_LIFECYCLES = {"active", "deferred"}
PACK_KINDS = {"core", "domain", "extension"}
CAPABILITY_LIFECYCLES = {"available", "planned", "deprecated"}
PACK_ROLES = {"foundation", "domain", "bridge", "extension"}
PACK_SCOPES = {"domain-neutral", "domain-specific", "cross-domain"}
PACK_MATURITIES = {"experimental", "preview", "stable", "legacy"}
DOCUMENTATION_TARGET_KINDS = {"repository-path", "external-url"}
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
NAMESPACE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")
LOCALIZATION_KEY_PATTERN = NAMESPACE_PATTERN

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
class PackClassification:
    family: str
    role: str
    scope: str
    domains: tuple[str, ...]
    bridge_pack_ids: tuple[str, ...]


@dataclass(frozen=True)
class PresentationEntry:
    id: str
    label: str
    description: str


@dataclass(frozen=True)
class DocumentationEntry:
    id: str
    label: str
    target_kind: str
    target: str


@dataclass(frozen=True)
class VisualIdentity:
    icon_id: str | None
    accent_token: str | None


@dataclass(frozen=True)
class PackPresentation:
    localization_key: str
    default_locale: str
    label: str
    short_description: str
    long_description: str
    maturity: str
    intended_audiences: tuple[PresentationEntry, ...]
    use_cases: tuple[PresentationEntry, ...]
    examples: tuple[PresentationEntry, ...]
    prerequisites: tuple[PresentationEntry, ...]
    provided_behaviors: tuple[PresentationEntry, ...]
    exclusions: tuple[PresentationEntry, ...]
    documentation: tuple[DocumentationEntry, ...]
    search_keywords: tuple[str, ...]
    visual: VisualIdentity | None


@dataclass(frozen=True)
class CapabilityPresentation:
    localization_key: str
    label: str
    description: str


@dataclass(frozen=True)
class CapabilityConfig:
    id: str
    lifecycle: str
    label: str | None
    description: str | None
    presentation: CapabilityPresentation | None = None


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
    classification: PackClassification | None
    presentation: PackPresentation | None
    dependencies: tuple[SchemaPackDependency, ...]
    capabilities: tuple[str, ...]
    capability_definitions: dict[str, CapabilityConfig]
    controlled_values: dict[str, tuple[str, ...]]
    controlled_value_definitions: dict[str, dict[str, ControlledValueConfig]]
    semantic_declarations: SemanticDeclarations


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


def _stable_string_list(mapping: dict, key: str, context: str) -> tuple[str, ...]:
    values = require_string_list(mapping, key, context)
    seen: set[str] = set()
    for value in values:
        validate_id(value, f"{context}.{key}")
        if value in seen:
            raise ValueError(f"Schema-pack configuration `{context}.{key}` contains duplicate `{value}`.")
        seen.add(value)
    return values


def _parse_presentation_entries(
    presentation: dict,
    key: str,
    context: str,
    *,
    required: bool,
) -> tuple[PresentationEntry, ...]:
    raw_entries = presentation.get(key)
    if not isinstance(raw_entries, list) or (required and not raw_entries):
        qualifier = "a non-empty" if required else "a"
        raise ValueError(f"Schema-pack configuration `{context}.{key}` must be {qualifier} list.")
    entries: list[PresentationEntry] = []
    seen: set[str] = set()
    for index, raw_entry in enumerate(raw_entries):
        entry_context = f"{context}.{key}[{index}]"
        entry = require_mapping(raw_entry, entry_context)
        assert_allowed_keys(entry, {"id", "label", "description"}, f"Schema pack `{entry_context}`")
        entry_id = require_string(entry, "id", entry_context)
        validate_id(entry_id, f"{entry_context}.id")
        if entry_id in seen:
            raise ValueError(f"Schema-pack configuration `{context}.{key}` contains duplicate `{entry_id}`.")
        seen.add(entry_id)
        entries.append(
            PresentationEntry(
                entry_id,
                require_string(entry, "label", entry_context),
                require_string(entry, "description", entry_context),
            )
        )
    return tuple(entries)


def _parse_documentation_entries(presentation: dict, context: str) -> tuple[DocumentationEntry, ...]:
    raw_entries = presentation.get("documentation")
    if not isinstance(raw_entries, list):
        raise ValueError(f"Schema-pack configuration `{context}.documentation` must be a list.")
    entries: list[DocumentationEntry] = []
    seen: set[str] = set()
    for index, raw_entry in enumerate(raw_entries):
        entry_context = f"{context}.documentation[{index}]"
        entry = require_mapping(raw_entry, entry_context)
        assert_allowed_keys(
            entry,
            {"id", "label", "target_kind", "target"},
            f"Schema pack `{entry_context}`",
        )
        entry_id = require_string(entry, "id", entry_context)
        validate_id(entry_id, f"{entry_context}.id")
        if entry_id in seen:
            raise ValueError(f"Schema-pack configuration `{context}.documentation` contains duplicate `{entry_id}`.")
        seen.add(entry_id)
        target_kind = require_string(entry, "target_kind", entry_context)
        if target_kind not in DOCUMENTATION_TARGET_KINDS:
            raise ValueError(f"Schema-pack configuration `{entry_context}.target_kind` is unsupported.")
        target = require_string(entry, "target", entry_context)
        if target_kind == "repository-path":
            path = Path(target)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Schema-pack configuration `{entry_context}.target` must remain repository-relative.")
            target = path.as_posix()
        else:
            parsed = urlparse(target)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                raise ValueError(f"Schema-pack configuration `{entry_context}.target` must be an absolute HTTPS URL.")
        entries.append(
            DocumentationEntry(
                entry_id,
                require_string(entry, "label", entry_context),
                target_kind,
                target,
            )
        )
    return tuple(entries)


def _parse_visual_identity(presentation: dict, context: str) -> VisualIdentity | None:
    raw_visual = presentation.get("visual")
    if raw_visual is None:
        return None
    visual = require_mapping(raw_visual, f"{context}.visual")
    assert_allowed_keys(visual, {"icon_id", "accent_token"}, f"Schema pack `{context}.visual`")
    icon_id = _optional_string(visual, "icon_id", f"{context}.visual")
    accent_token = _optional_string(visual, "accent_token", f"{context}.visual")
    if icon_id is None and accent_token is None:
        raise ValueError(f"Schema-pack configuration `{context}.visual` must declare at least one identifier.")
    for key, value in (("icon_id", icon_id), ("accent_token", accent_token)):
        if value is not None:
            validate_id(value, f"{context}.visual.{key}")
    return VisualIdentity(icon_id, accent_token)


def _parse_pack_classification(pack: dict, pack_id: str) -> PackClassification:
    context = f"{pack_id}.classification"
    classification = require_mapping(pack.get("classification"), context)
    assert_allowed_keys(
        classification,
        {"family", "role", "scope", "domains", "bridge_pack_ids"},
        f"Schema pack `{context}`",
    )
    family = require_string(classification, "family", context)
    validate_id(family, f"{context}.family")
    role = require_string(classification, "role", context)
    if role not in PACK_ROLES:
        raise ValueError(f"Schema-pack configuration `{context}.role` is unsupported.")
    scope = require_string(classification, "scope", context)
    if scope not in PACK_SCOPES:
        raise ValueError(f"Schema-pack configuration `{context}.scope` is unsupported.")
    domains = _stable_string_list(classification, "domains", context)
    bridge_ids = _stable_string_list(classification, "bridge_pack_ids", context)
    if scope == "domain-neutral" and domains:
        raise ValueError(f"Schema-pack configuration `{context}.domains` must be empty for domain-neutral scope.")
    if scope == "domain-specific" and not domains:
        raise ValueError(f"Schema-pack configuration `{context}.domains` must identify at least one domain.")
    if scope == "cross-domain" and len(domains) < 2:
        raise ValueError(f"Schema-pack configuration `{context}.domains` must identify at least two domains.")
    if role == "bridge":
        if scope != "cross-domain" or len(bridge_ids) < 2:
            raise ValueError(
                f"Schema-pack configuration `{context}` bridges require cross-domain scope and at least two joins."
            )
    elif bridge_ids:
        raise ValueError(f"Schema-pack configuration `{context}.bridge_pack_ids` is only valid for bridges.")
    return PackClassification(family, role, scope, domains, bridge_ids)


def _parse_pack_presentation(pack: dict, pack_id: str) -> PackPresentation:
    context = f"{pack_id}.presentation"
    presentation = require_mapping(pack.get("presentation"), context)
    assert_allowed_keys(
        presentation,
        {
            "localization_key",
            "default_locale",
            "label",
            "short_description",
            "long_description",
            "maturity",
            "intended_audiences",
            "use_cases",
            "examples",
            "prerequisites",
            "provided_behaviors",
            "exclusions",
            "documentation",
            "search_keywords",
            "visual",
        },
        f"Schema pack `{context}`",
    )
    localization_key = require_string(presentation, "localization_key", context)
    if not LOCALIZATION_KEY_PATTERN.fullmatch(localization_key):
        raise ValueError(f"Schema-pack configuration `{context}.localization_key` must be a dotted stable key.")
    default_locale = require_string(presentation, "default_locale", context)
    if default_locale != "en":
        raise ValueError(f"Schema-pack configuration `{context}.default_locale` must currently be `en`.")
    maturity = require_string(presentation, "maturity", context)
    if maturity not in PACK_MATURITIES:
        raise ValueError(f"Schema-pack configuration `{context}.maturity` is unsupported.")
    raw_keywords = presentation.get("search_keywords")
    if not isinstance(raw_keywords, list) or any(
        not isinstance(item, str) or not item.strip() for item in raw_keywords
    ):
        raise ValueError(f"Schema-pack configuration `{context}.search_keywords` must be a list of strings.")
    keywords = tuple(item.strip() for item in raw_keywords)
    if len({item.casefold() for item in keywords}) != len(keywords):
        raise ValueError(f"Schema-pack configuration `{context}.search_keywords` contains duplicates.")
    return PackPresentation(
        localization_key,
        default_locale,
        require_string(presentation, "label", context),
        require_string(presentation, "short_description", context),
        require_string(presentation, "long_description", context),
        maturity,
        _parse_presentation_entries(presentation, "intended_audiences", context, required=True),
        _parse_presentation_entries(presentation, "use_cases", context, required=True),
        _parse_presentation_entries(presentation, "examples", context, required=False),
        _parse_presentation_entries(presentation, "prerequisites", context, required=False),
        _parse_presentation_entries(presentation, "provided_behaviors", context, required=True),
        _parse_presentation_entries(presentation, "exclusions", context, required=True),
        _parse_documentation_entries(presentation, context),
        keywords,
        _parse_visual_identity(presentation, context),
    )


def _parse_capability_presentation(raw: dict, context: str) -> CapabilityPresentation:
    presentation = require_mapping(raw.get("presentation"), f"{context}.presentation")
    assert_allowed_keys(
        presentation,
        {"localization_key", "label", "description"},
        f"Schema pack `{context}.presentation`",
    )
    localization_key = require_string(presentation, "localization_key", f"{context}.presentation")
    if not LOCALIZATION_KEY_PATTERN.fullmatch(localization_key):
        raise ValueError(
            f"Schema-pack configuration `{context}.presentation.localization_key` must be a dotted stable key."
        )
    return CapabilityPresentation(
        localization_key,
        require_string(presentation, "label", f"{context}.presentation"),
        require_string(presentation, "description", f"{context}.presentation"),
    )


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
    data = load_yaml_file(path, "schema pack", expected_schema_version=SUPPORTED_SCHEMA_PACK_VERSIONS)
    pack = require_mapping(data, expected_pack_id)
    schema_version = require_positive_int(pack, "schema_version", expected_pack_id)
    legacy = schema_version == 4
    allowed_keys = {
        "schema_version",
        "pack_id",
        "pack_version",
        "lifecycle",
        "pack_kind",
        "dependencies",
        "capabilities",
        "controlled_values",
        "semantic_declarations",
    }
    allowed_keys.update({"label", "description"} if legacy else {"classification", "presentation"})
    assert_allowed_keys(
        pack,
        allowed_keys,
        f"Schema pack `{expected_pack_id}`",
    )
    if schema_version not in SUPPORTED_SCHEMA_PACK_VERSIONS:
        raise ValueError(
            f"Unsupported schema-pack schema_version {schema_version!r} in {path}; "
            f"expected one of {SUPPORTED_SCHEMA_PACK_VERSIONS}."
        )
    pack_id = require_string(pack, "pack_id", expected_pack_id)
    validate_id(pack_id, f"{expected_pack_id}.pack_id")
    if pack_id != expected_pack_id:
        raise ValueError(f"Schema-pack selection `{expected_pack_id}` loads pack `{pack_id}`.")
    pack_version = require_positive_int(pack, "pack_version", pack_id)
    pack_lifecycle = require_string(pack, "lifecycle", pack_id)
    if pack_lifecycle not in PACK_LIFECYCLES:
        raise ValueError(f"Schema pack `{pack_id}.lifecycle` must be one of: {', '.join(sorted(PACK_LIFECYCLES))}.")
    kind = require_string(pack, "pack_kind", pack_id)
    if kind not in PACK_KINDS:
        raise ValueError(f"Schema pack `{pack_id}.pack_kind` must be one of: {', '.join(sorted(PACK_KINDS))}.")
    classification = None if legacy else _parse_pack_classification(pack, pack_id)
    presentation = None if legacy else _parse_pack_presentation(pack, pack_id)
    pack_label = require_string(pack, "label", pack_id) if legacy else presentation.label
    pack_description = require_string(pack, "description", pack_id) if legacy else presentation.short_description

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
    if not isinstance(raw_capabilities, list):
        raise ValueError(f"Schema pack `{pack_id}.capabilities` must be a list.")
    capabilities: list[str] = []
    capability_definitions: dict[str, CapabilityConfig] = {}
    for index, raw_capability in enumerate(raw_capabilities):
        context = f"{pack_id}.capabilities[{index}]"
        if isinstance(raw_capability, str):
            if not legacy:
                raise ValueError(
                    f"Schema-pack configuration `{context}` must be a capability-definition mapping in schema 5."
                )
            capability_id = raw_capability.strip()
            lifecycle = "available"
            label = None
            description = None
            capability_presentation = None
        elif isinstance(raw_capability, dict):
            allowed_capability_keys = (
                {"id", "lifecycle", "label", "description"}
                if legacy
                else {
                    "id",
                    "lifecycle",
                    "presentation",
                }
            )
            assert_allowed_keys(
                raw_capability,
                allowed_capability_keys,
                f"Schema pack `{context}`",
            )
            capability_id = require_string(raw_capability, "id", context)
            lifecycle = require_string(raw_capability, "lifecycle", context)
            if legacy:
                label_value = raw_capability.get("label")
                description_value = raw_capability.get("description")
                for key, value in (("label", label_value), ("description", description_value)):
                    if value is not None and (not isinstance(value, str) or not value.strip()):
                        raise ValueError(
                            f"Schema-pack configuration `{context}.{key}` must be a non-empty string when present."
                        )
                label = label_value.strip() if isinstance(label_value, str) else None
                description = description_value.strip() if isinstance(description_value, str) else None
                capability_presentation = None
            else:
                capability_presentation = _parse_capability_presentation(raw_capability, context)
                label = capability_presentation.label
                description = capability_presentation.description
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
            presentation=capability_presentation,
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
        lifecycle=pack_lifecycle,
        kind=kind,
        label=pack_label,
        description=pack_description,
        classification=classification,
        presentation=presentation,
        dependencies=tuple(dependencies),
        capabilities=tuple(capabilities),
        capability_definitions=capability_definitions,
        controlled_values=controlled_values,
        controlled_value_definitions=controlled_value_definitions,
        semantic_declarations=parse_semantic_declarations(pack, pack_id),
    )


def _validate_pack_presentation_composition(
    packs: dict[str, SchemaPackConfig],
    selection_order: list[str],
) -> None:
    versions = {pack.schema_version for pack in packs.values()}
    if versions == {4}:
        return
    if versions != {CURRENT_SCHEMA_PACK_VERSION}:
        raise ValueError("Schema-pack composition must not mix legacy schema 4 and presentation schema 5 packs.")

    localization_owners: dict[str, str] = {}
    capability_presentations: dict[str, CapabilityPresentation] = {}
    for pack_id in selection_order:
        pack = packs[pack_id]
        classification = pack.classification
        presentation = pack.presentation
        if classification is None or presentation is None:
            raise ValueError(f"Schema pack `{pack_id}` is missing schema-5 presentation metadata.")
        prior_owner = localization_owners.get(presentation.localization_key)
        if prior_owner is not None:
            raise ValueError(
                f"Schema-pack localization key `{presentation.localization_key}` is shared by "
                f"`{prior_owner}` and `{pack_id}`."
            )
        localization_owners[presentation.localization_key] = f"pack:{pack_id}"

        dependency_ids = {dependency.pack_id for dependency in pack.dependencies}
        if classification.scope == "domain-neutral":
            nonneutral = [
                dependency_id
                for dependency_id in dependency_ids
                if packs[dependency_id].classification is None
                or packs[dependency_id].classification.scope != "domain-neutral"
            ]
            if nonneutral:
                raise ValueError(
                    f"Domain-neutral schema pack `{pack_id}` depends on domain-facing pack(s): "
                    f"{', '.join(sorted(nonneutral))}."
                )
        elif classification.scope == "domain-specific":
            incompatible = []
            own_domains = set(classification.domains)
            for dependency_id in dependency_ids:
                dependency_classification = packs[dependency_id].classification
                if dependency_classification is None or dependency_classification.scope == "domain-neutral":
                    continue
                if not own_domains.intersection(dependency_classification.domains):
                    incompatible.append(dependency_id)
            if incompatible:
                raise ValueError(
                    f"Domain-specific schema pack `{pack_id}` has incompatible dependency scope: "
                    f"{', '.join(sorted(incompatible))}."
                )

        if classification.role == "bridge":
            bridge_ids = set(classification.bridge_pack_ids)
            if not bridge_ids <= dependency_ids:
                missing = sorted(bridge_ids - dependency_ids)
                raise ValueError(f"Bridge schema pack `{pack_id}` joins nondependency pack(s): {', '.join(missing)}.")
            joinable_dependencies = {
                dependency_id
                for dependency_id in dependency_ids
                if packs[dependency_id].classification is not None
                and packs[dependency_id].classification.role in {"foundation", "domain"}
            }
            if bridge_ids != joinable_dependencies:
                raise ValueError(f"Bridge schema pack `{pack_id}` must declare every joined foundation or domain.")
            joined_domains: set[str] = set()
            for dependency_id in bridge_ids:
                joined = packs[dependency_id].classification
                if joined is None:
                    raise ValueError(f"Bridge schema pack `{pack_id}` joins an unclassified pack.")
                joined_domains.update(joined.domains or (joined.family,))
            if set(classification.domains) != joined_domains:
                raise ValueError(f"Bridge schema pack `{pack_id}` domains do not match its declared joins.")
        elif classification.scope == "cross-domain":
            raise ValueError(f"Cross-domain schema pack `{pack_id}` must use the bridge role.")

        for capability_id in pack.capabilities:
            capability_presentation = pack.capability_definitions[capability_id].presentation
            if capability_presentation is None:
                raise ValueError(f"Schema pack `{pack_id}` capability `{capability_id}` lacks presentation metadata.")
            owner_key = localization_owners.get(capability_presentation.localization_key)
            expected_owner = f"capability:{capability_id}"
            if owner_key is not None and owner_key != expected_owner:
                raise ValueError(
                    f"Schema-pack localization key `{capability_presentation.localization_key}` "
                    f"conflicts with `{owner_key}`."
                )
            localization_owners[capability_presentation.localization_key] = expected_owner
            prior = capability_presentations.get(capability_id)
            if prior is not None and prior != capability_presentation:
                raise ValueError(f"Capability `{capability_id}` providers declare conflicting presentation metadata.")
            capability_presentations[capability_id] = capability_presentation


def load_schema_pack_registry(
    project: ProjectConfig,
    *,
    installed_packs: dict[str, SchemaPackConfig] | None = None,
) -> SchemaPackRegistry:
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
        if installed_packs is None:
            packs[pack_id] = load_pack(pack_path, pack_id)
        else:
            installed = installed_packs.get(pack_id)
            if installed is None:
                raise ValueError(f"Schema-pack registry selects pack `{pack_id}` that is not installed.")
            if installed.path.resolve() != pack_path.resolve():
                raise ValueError(
                    f"Schema-pack registry path for `{pack_id}` does not match the installed catalog path."
                )
            packs[pack_id] = installed
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

    _validate_pack_presentation_composition(packs, selection_order)

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


def load_schema_pack_registry_from_catalog(project: ProjectConfig, catalog: object) -> SchemaPackRegistry:
    config = getattr(catalog, "config", None)
    installed_packs = getattr(catalog, "pack_configs", None)
    if config is None or installed_packs is None:
        raise TypeError("Catalog-backed schema-pack loading requires a validated FrameworkCatalog.")
    if project.framework != config.framework_id:
        raise ValueError(
            f"Project framework `{project.framework}` does not match installed framework `{config.framework_id}`."
        )
    if project.lookup_keys_registry.resolve() != config.lookup_keys_registry.resolve():
        raise ValueError("Project lookup-key registry does not match the framework installation lookup-key registry.")
    return load_schema_pack_registry(project, installed_packs=installed_packs)
