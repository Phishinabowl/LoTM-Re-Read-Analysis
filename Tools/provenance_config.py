from dataclasses import dataclass
from pathlib import Path
import re

from entity_config import EntityRegistry
from project_config import ProjectConfig
from reconciliation_config import ReconciliationRegistry
from schema_pack_config import SchemaPackRegistry, load_schema_pack_registry
from source_config import (
    ApplicabilityDecision,
    ApplicabilityScopeMatch,
    AuthorityCandidateDecision,
    SourceRegistry,
    TemporalWindow,
    compare_positions,
    applicability_temporal_match,
    normalize_effective_at,
    parse_temporal_window,
    require_mapping,
    require_string,
    require_string_list,
    validate_id,
    validate_pack_values,
    validate_source_position,
)
from strict_yaml import assert_allowed_keys, load_yaml_file


SUPPORTED_PROVENANCE_SCHEMA_VERSION = 1
FIELD_PATH_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*(?:(?:\.[a-z][a-z0-9_]*)|(?:\[[0-9]+\]))*$"
)


@dataclass(frozen=True)
class EvidenceLocator:
    id: str
    medium_id: str
    evidence_mode: str
    locator_type: str
    position: dict[str, object] | None
    start: dict[str, object] | None
    end: dict[str, object] | None


@dataclass(frozen=True)
class ProvenanceEvidenceLink:
    source_id: str
    evidence_role: str
    locators: tuple[EvidenceLocator, ...]


@dataclass(frozen=True)
class ProvenanceAssertion:
    id: str
    claim_key: str
    subject_type: str
    subject_id: str
    claim_namespace: str
    field_path: str | None
    asserted_value: object
    assertion_status: str
    observed_at: TemporalWindow | None
    effective_window: TemporalWindow | None
    evidence_links: tuple[ProvenanceEvidenceLink, ...]


@dataclass(frozen=True)
class ClaimSupersession:
    id: str
    source_claim_key: str
    relationship_type: str
    target_claim_key: str
    applicability_scope_id: str
    continuity_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClaimAuthorityEvaluation:
    outcome: str
    profile_id: str
    claim_key: str
    best_rank: int | None
    winning_assertion_ids: tuple[str, ...]
    decisions: tuple[AuthorityCandidateDecision, ...]


@dataclass(frozen=True)
class ProvenanceRegistry:
    path: Path
    schema_version: int
    assertions: tuple[ProvenanceAssertion, ...]
    claim_supersessions: tuple[ClaimSupersession, ...]
    sources: SourceRegistry
    entities: EntityRegistry
    reconciliations: ReconciliationRegistry

    def assertions_for_claim(self, claim_key: str) -> tuple[ProvenanceAssertion, ...]:
        return tuple(item for item in self.assertions if item.claim_key == claim_key)

    def provenance_target(self, subject_type: str, subject_id: str) -> object:
        if subject_type == "claim-supersession":
            matches = [item for item in self.claim_supersessions if item.id == subject_id]
            if not matches:
                raise ValueError(f"Unknown claim-supersession `{subject_id}`.")
            return matches[0]
        source_targets = self.sources.provenance_targets()
        entity_targets = self.entities.provenance_targets()
        reconciliation_targets = self.reconciliations.provenance_targets()
        if subject_type in source_targets:
            return self.sources.provenance_target(subject_type, subject_id)
        if subject_type in entity_targets:
            return self.entities.provenance_target(subject_type, subject_id)
        if subject_type in reconciliation_targets:
            return self.reconciliations.provenance_target(subject_type, subject_id)
        raise ValueError(f"Unsupported provenance subject type `{subject_type}`.")

    def evaluate_claim_authority(
        self, profile_id: str, claim_key: str
    ) -> ClaimAuthorityEvaluation:
        assertions = self.assertions_for_claim(claim_key)
        if not assertions:
            raise ValueError(f"Unknown claim key `{claim_key}`.")
        claim_namespace = assertions[0].claim_namespace
        decisions = tuple(
            AuthorityCandidateDecision(
                f"{assertion.id}:{link.source_id}:{locator.id}",
                assertion.id,
                self.sources.authority_decision(
                    profile_id, claim_namespace, link.source_id, locator.evidence_mode
                ),
            )
            for assertion in assertions
            for link in assertion.evidence_links
            if link.evidence_role == "supports"
            for locator in link.locators
        )
        if not decisions:
            raise ValueError(f"Claim key `{claim_key}` has no supporting evidence locators.")
        comparison_groups = {
            self.sources.sources[item.decision.source_id].comparison_group
            for item in decisions
        }
        if len(comparison_groups) != 1:
            return ClaimAuthorityEvaluation(
                "incomparable", profile_id, claim_key, None, (), decisions
            )
        profile = self.sources.authority_profiles[profile_id]
        best_by_assertion: dict[str, int] = {}
        for item in decisions:
            assertion_id = str(item.assertion_id)
            previous = best_by_assertion.get(assertion_id)
            rank = item.decision.rank
            if previous is None or (
                profile.source_priority_order == "ascending" and rank < previous
            ) or (
                profile.source_priority_order == "descending" and rank > previous
            ):
                best_by_assertion[assertion_id] = rank
        best_rank = (
            min(best_by_assertion.values())
            if profile.source_priority_order == "ascending"
            else max(best_by_assertion.values())
        )
        winners = tuple(
            item.id
            for item in assertions
            if best_by_assertion.get(item.id) == best_rank
        )
        values = [item.asserted_value for item in assertions if item.id in winners]
        outcome = "winner" if len(winners) == 1 else (
            "tie" if all(value == values[0] for value in values[1:]) else "conflict"
        )
        return ClaimAuthorityEvaluation(
            outcome, profile_id, claim_key, best_rank, winners, decisions
        )

    def applicability_decision(
        self,
        target_type: str,
        target_id: str,
        *,
        territory_id: str | None = None,
        effective_at: str | object | None = None,
    ) -> ApplicabilityDecision:
        if target_type != "provenance-claim":
            return self.sources.applicability_decision(
                target_type,
                target_id,
                territory_id=territory_id,
                effective_at=effective_at,
            )
        assertions = self.assertions_for_claim(target_id)
        if not assertions:
            raise ValueError(f"Unknown provenance-claim applicability target `{target_id}`.")
        if territory_id is not None and territory_id not in self.sources.territories:
            raise ValueError(f"Unknown territory `{territory_id}`.")
        effective_instant, effective_label = normalize_effective_at(effective_at)
        subject_type = assertions[0].subject_type
        subject_id = assertions[0].subject_id
        matches: list[ApplicabilityScopeMatch] = []
        for scope in self.sources.applicability_scopes.values():
            if scope.target_type == "provenance-claim" and scope.target_id == target_id:
                target_match = "exact"
            else:
                subject_match = self.sources._applicability_target_match(
                    scope.target_type,
                    scope.target_id,
                    subject_type,
                    subject_id,
                    set(),
                )
                if subject_match is None:
                    continue
                target_match = "claim-subject"
            territory_match = self.sources._applicability_territory_match(
                scope, territory_id
            )
            if territory_match is None:
                continue
            temporal_match = applicability_temporal_match(
                scope.effective_window, effective_instant
            )
            if temporal_match is None:
                continue
            matches.append(ApplicabilityScopeMatch(
                scope.id,
                "indeterminate" if temporal_match == "unknown" else "applicable",
                target_match,
                territory_match,
                temporal_match,
                scope.precedence,
            ))
        matches.sort(key=lambda item: (-item.precedence, item.scope_id))
        applicable = [item for item in matches if item.outcome == "applicable"]
        highest = applicable[0].precedence if applicable else None
        winners = tuple(
            item.scope_id for item in applicable if item.precedence == highest
        )
        return ApplicabilityDecision(
            target_type,
            target_id,
            territory_id,
            effective_label,
            tuple(item.scope_id for item in applicable),
            tuple(item.scope_id for item in matches if item.outcome == "indeterminate"),
            winners,
            highest,
            len(winners) > 1,
            tuple(matches),
        )


def optional_string(mapping: dict, key: str, context: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Provenance registry `{context}.{key}` must be a non-empty string or null.")
    return value.strip()


def resolve_provenance_field_path(record: object, field_path: str, context: str) -> object:
    current = record
    for token in re.findall(r"[a-z][a-z0-9_]*|\[[0-9]+\]", field_path):
        if token.startswith("["):
            index = int(token[1:-1])
            if not isinstance(current, (list, tuple)) or index >= len(current):
                raise ValueError(f"Provenance registry `{context}` does not resolve on its subject.")
            current = current[index]
        elif isinstance(current, dict) and token in current:
            current = current[token]
        elif hasattr(current, token):
            current = getattr(current, token)
        else:
            raise ValueError(f"Provenance registry `{context}` does not resolve on its subject.")
    return current


def validate_locator_coverage(
    sources: SourceRegistry,
    source_id: str,
    medium_id: str,
    evidence_mode: str,
    positions: tuple[dict[str, object], ...],
    context: str,
) -> None:
    source = sources.sources[source_id]
    medium = sources.mediums[medium_id]
    work_id = str(positions[0][medium.work_scope_field])
    if work_id not in source.work_ids:
        raise ValueError(
            f"Provenance registry `{context}` falls outside the evidence source's work scope."
        )
    def segment_id(position: dict[str, object]) -> str | None:
        validation = medium.structural_validation
        if validation is None or validation.strategy != "work-segment-ordering":
            return None
        return str(position[validation.segment_field])

    def target_segments(target_type: str, target_id: str) -> set[str]:
        if target_type == "segment":
            return {target_id}
        if target_type == "content-group":
            return {
                segment
                for member in sources.content_groups[target_id].members
                for segment in target_segments(member.target_type, member.target_id)
            }
        if target_type == "manifestation":
            return set(sources.manifestations[target_id].segment_ids)
        if target_type == "release-component":
            return set(sources.release_components[target_id].segment_ids)
        if target_type == "release-package":
            package = sources.release_packages[target_id]
            result = set(package.segment_ids)
            for component_id in package.release_component_ids:
                result.update(sources.release_components[component_id].segment_ids)
            for manifestation_id in package.manifestation_ids:
                result.update(sources.manifestations[manifestation_id].segment_ids)
            return result
        return set()

    def complete_work_scope(target_type: str, target_id: str) -> set[str]:
        if target_type == "work":
            return {target_id}
        if target_type == "content-group":
            return {
                work
                for member in sources.content_groups[target_id].members
                for work in complete_work_scope(member.target_type, member.target_id)
            }
        if target_type == "manifestation":
            item = sources.manifestations[target_id]
            return {item.work_id} if not item.segment_ids else set()
        if target_type == "release-component":
            item = sources.release_components[target_id]
            if item.segment_ids or item.manifestation_id is None:
                return set()
            return complete_work_scope("manifestation", item.manifestation_id)
        if target_type == "release-package":
            package = sources.release_packages[target_id]
            result: set[str] = set()
            for manifestation_id in package.manifestation_ids:
                result.update(complete_work_scope("manifestation", manifestation_id))
            for component_id in package.release_component_ids:
                result.update(complete_work_scope("release-component", component_id))
            return result
        return set()

    if source.coverage:
        covered = False
        for coverage in source.coverage:
            if coverage.medium_id != medium_id or evidence_mode not in coverage.evidence_modes:
                continue
            if work_id not in sources.target_work_ids(coverage.target_type, coverage.target_id):
                continue
            for position_range in coverage.position_ranges:
                fields = set(position_range.start)
                if any(not fields.issubset(position) for position in positions):
                    continue
                if all(
                    compare_positions(position_range.start, {field: position[field] for field in fields}, medium, sources.ordering_schemes, context) <= 0
                    and compare_positions({field: position[field] for field in fields}, position_range.end, medium, sources.ordering_schemes, context) <= 0
                    for position in positions
                ):
                    covered = True
                    break
            if covered:
                break
            position_segments = {segment_id(position) for position in positions}
            if (
                coverage.coverage_type == "complete"
                and not coverage.position_ranges
                and work_id in complete_work_scope(coverage.target_type, coverage.target_id)
            ) or (
                None not in position_segments
                and position_segments.issubset(target_segments(coverage.target_type, coverage.target_id))
            ):
                covered = True
                break
        if not covered:
            raise ValueError(
                f"Provenance registry `{context}` falls outside the evidence source's declared coverage."
            )

    scope_sets: list[set[str]] = []
    if source.manifestation_id is not None:
        scope = set(sources.manifestations[source.manifestation_id].segment_ids)
        if scope:
            scope_sets.append(scope)
    for component_id in source.release_component_ids:
        scope = set(sources.release_components[component_id].segment_ids)
        if scope:
            scope_sets.append(scope)
    if source.release_package_id is not None:
        package = sources.release_packages[source.release_package_id]
        if package.segment_ids and not package.manifestation_ids:
            scope_sets.append(set(package.segment_ids))
    if scope_sets:
        position_segments = {segment_id(position) for position in positions}
        if None in position_segments or any(
            not position_segments.issubset(scope) for scope in scope_sets
        ):
            raise ValueError(
                f"Provenance registry `{context}` falls outside the evidence source's segment scope."
            )


def parse_locator(
    raw_locator: object,
    context: str,
    source_id: str,
    sources: SourceRegistry,
    schema_packs: SchemaPackRegistry,
) -> EvidenceLocator:
    locator = require_mapping(raw_locator, context)
    assert_allowed_keys(
        locator,
        {"id", "medium_id", "evidence_mode", "locator_type", "position", "start", "end"},
        f"Provenance registry `{context}`",
    )
    locator_id = require_string(locator, "id", context)
    validate_id(locator_id, f"{context}.id")
    medium_id = require_string(locator, "medium_id", context)
    if medium_id not in sources.mediums:
        raise ValueError(f"Provenance registry `{context}.medium_id` references unknown medium `{medium_id}`.")
    source = sources.sources[source_id]
    if medium_id not in source.locator_medium_ids:
        raise ValueError(f"Provenance registry `{context}.medium_id` is not allowed by the evidence source.")
    evidence_mode = require_string(locator, "evidence_mode", context)
    if evidence_mode not in source.evidence_modes:
        raise ValueError(f"Provenance registry `{context}.evidence_mode` is not declared by the evidence source.")
    locator_type = require_string(locator, "locator_type", context)
    validate_pack_values(
        schema_packs, "provenance.locator-type", (locator_type,), f"{context}.locator_type"
    )
    medium = sources.mediums[medium_id]
    if locator_type == "point":
        if "start" in locator or "end" in locator:
            raise ValueError(f"Provenance registry `{context}` point locator cannot declare start or end.")
        position = require_mapping(locator.get("position"), f"{context}.position")
        validate_source_position(
            position, medium, source.work_ids, sources.works, sources.segments,
            sources.ordering_schemes, f"{context}.position"
        )
        validate_locator_coverage(
            sources, source_id, medium_id, evidence_mode, (position,), context
        )
        return EvidenceLocator(locator_id, medium_id, evidence_mode, locator_type, dict(position), None, None)
    if "position" in locator:
        raise ValueError(f"Provenance registry `{context}` range locator cannot declare position.")
    start = require_mapping(locator.get("start"), f"{context}.start")
    end = require_mapping(locator.get("end"), f"{context}.end")
    if set(start) != set(end):
        raise ValueError(f"Provenance registry `{context}` range start/end fields must be identical.")
    for value, label in ((start, "start"), (end, "end")):
        validate_source_position(
            value, medium, source.work_ids, sources.works, sources.segments,
            sources.ordering_schemes, f"{context}.{label}"
        )
    if start[medium.work_scope_field] != end[medium.work_scope_field]:
        raise ValueError(f"Provenance registry `{context}` range endpoints must identify the same work.")
    if compare_positions(start, end, medium, sources.ordering_schemes, context) > 0:
        raise ValueError(f"Provenance registry `{context}` range start must not follow end.")
    validate_locator_coverage(
        sources, source_id, medium_id, evidence_mode, (start, end), context
    )
    return EvidenceLocator(locator_id, medium_id, evidence_mode, locator_type, None, dict(start), dict(end))


def load_provenance_registry(
    project: ProjectConfig,
    sources: SourceRegistry,
    entities: EntityRegistry,
    reconciliations: ReconciliationRegistry,
    schema_packs: SchemaPackRegistry | None = None,
) -> ProvenanceRegistry:
    if schema_packs is None:
        schema_packs = load_schema_pack_registry(project)
    data = load_yaml_file(project.provenance_registry, "provenance registry", expected_schema_version=SUPPORTED_PROVENANCE_SCHEMA_VERSION)
    registry = require_mapping(data, "root")
    assert_allowed_keys(
        registry,
        {"schema_version", "claim_supersessions", "assertions"},
        "Provenance registry root",
    )
    schema_version = registry.get("schema_version")
    if schema_version != SUPPORTED_PROVENANCE_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported provenance schema_version {schema_version!r}; expected {SUPPORTED_PROVENANCE_SCHEMA_VERSION}."
        )

    provider_types = (
        set(sources.provenance_targets()),
        set(entities.provenance_targets()),
        set(reconciliations.provenance_targets()),
    )
    duplicated_subject_types = set()
    for index, provider in enumerate(provider_types):
        for other in provider_types[index + 1:]:
            duplicated_subject_types |= provider & other
    if duplicated_subject_types:
        raise ValueError(
            "Provenance subject types have multiple providers: "
            + ", ".join(sorted(duplicated_subject_types))
            + "."
        )
    provided_subject_types = (
        set(sources.provenance_targets())
        | set(entities.provenance_targets())
        | set(reconciliations.provenance_targets())
        | {"claim-supersession"}
    )
    allowed_subject_types = set(
        schema_packs.allowed_values("provenance.subject-type")
    )
    missing_providers = allowed_subject_types - provided_subject_types
    unregistered_providers = provided_subject_types - allowed_subject_types
    if missing_providers or unregistered_providers:
        details = []
        if missing_providers:
            details.append("missing providers: " + ", ".join(sorted(missing_providers)))
        if unregistered_providers:
            details.append(
                "unregistered providers: " + ", ".join(sorted(unregistered_providers))
            )
        raise ValueError("Provenance subject-provider mismatch (" + "; ".join(details) + ").")

    raw_supersessions = registry.get("claim_supersessions")
    if not isinstance(raw_supersessions, list):
        raise ValueError("Provenance registry `claim_supersessions` must be a list.")
    supersessions: list[ClaimSupersession] = []
    seen_supersession_ids: set[str] = set()
    for index, raw_item in enumerate(raw_supersessions):
        context = f"claim_supersessions[{index}]"
        item = require_mapping(raw_item, context)
        assert_allowed_keys(
            item,
            {"id", "source_claim_key", "target_claim_key", "relationship_type", "applicability_scope_id", "continuity_ids"},
            f"Provenance registry `{context}`",
        )
        item_id = require_string(item, "id", context)
        validate_id(item_id, f"{context}.id")
        if item_id in seen_supersession_ids:
            raise ValueError(f"Provenance registry claim-supersession ID `{item_id}` is duplicated.")
        seen_supersession_ids.add(item_id)
        source_claim_key = require_string(item, "source_claim_key", context)
        target_claim_key = require_string(item, "target_claim_key", context)
        validate_id(source_claim_key, f"{context}.source_claim_key")
        validate_id(target_claim_key, f"{context}.target_claim_key")
        if source_claim_key == target_claim_key:
            raise ValueError(f"Provenance registry `{context}` cannot supersede a claim with itself.")
        relationship_type = require_string(item, "relationship_type", context)
        validate_pack_values(
            schema_packs, "narrative.claim-change-type", (relationship_type,),
            f"{context}.relationship_type"
        )
        scope_id = require_string(item, "applicability_scope_id", context)
        if scope_id not in sources.applicability_scopes:
            raise ValueError(f"Provenance registry `{context}.applicability_scope_id` references unknown scope `{scope_id}`.")
        scope = sources.applicability_scopes[scope_id]
        if scope.target_type != "provenance-claim" or scope.target_id != target_claim_key:
            raise ValueError(f"Provenance registry `{context}` scope must target the superseded claim `{target_claim_key}`.")
        continuity_ids = require_string_list(item, "continuity_ids", context)
        unknown = set(continuity_ids) - set(sources.continuities)
        if unknown:
            raise ValueError(f"Provenance registry `{context}.continuity_ids` references unknown continuities: {', '.join(sorted(unknown))}.")
        supersessions.append(ClaimSupersession(item_id, source_claim_key, relationship_type, target_claim_key, scope_id, continuity_ids))

    raw_assertions = registry.get("assertions")
    if not isinstance(raw_assertions, list):
        raise ValueError("Provenance registry `assertions` must be a list.")
    assertions: list[ProvenanceAssertion] = []
    seen_assertion_ids: set[str] = set()
    seen_locator_ids: set[str] = set()
    claim_shapes: dict[str, tuple[str, str, str, str | None]] = {}
    supersession_targets = {item.id: item for item in supersessions}
    for index, raw_assertion in enumerate(raw_assertions):
        context = f"assertions[{index}]"
        assertion = require_mapping(raw_assertion, context)
        assert_allowed_keys(
            assertion,
            {"id", "claim_key", "subject_type", "subject_id", "claim_namespace", "field_path", "asserted_value", "assertion_status", "observed_at", "effective_window", "evidence_links"},
            f"Provenance registry `{context}`",
        )
        assertion_id = require_string(assertion, "id", context)
        validate_id(assertion_id, f"{context}.id")
        if assertion_id in seen_assertion_ids:
            raise ValueError(f"Provenance registry assertion ID `{assertion_id}` is duplicated.")
        seen_assertion_ids.add(assertion_id)
        claim_key = require_string(assertion, "claim_key", context)
        validate_id(claim_key, f"{context}.claim_key")
        subject_type = require_string(assertion, "subject_type", context)
        validate_pack_values(schema_packs, "provenance.subject-type", (subject_type,), f"{context}.subject_type")
        subject_id = require_string(assertion, "subject_id", context)
        if subject_type == "claim-supersession":
            target = supersession_targets.get(subject_id)
            if target is None:
                raise ValueError(f"Provenance registry `{context}.subject_id` references unknown claim-supersession `{subject_id}`.")
        elif subject_type in sources.provenance_targets():
            target = sources.provenance_target(subject_type, subject_id)
        elif subject_type in entities.provenance_targets():
            target = entities.provenance_target(subject_type, subject_id)
        elif subject_type in reconciliations.provenance_targets():
            target = reconciliations.provenance_target(subject_type, subject_id)
        else:
            raise ValueError(f"Unsupported provenance subject type `{subject_type}`.")
        claim_namespace = require_string(assertion, "claim_namespace", context)
        validate_pack_values(schema_packs, "provenance.claim-namespace", (claim_namespace,), f"{context}.claim_namespace")
        field_path = optional_string(assertion, "field_path", context)
        if field_path is not None:
            if not FIELD_PATH_PATTERN.fullmatch(field_path):
                raise ValueError(f"Provenance registry `{context}.field_path` must be a dotted/indexed machine field path.")
            resolve_provenance_field_path(target, field_path, f"{context}.field_path")
        shape = (subject_type, subject_id, claim_namespace, field_path)
        if claim_key in claim_shapes and claim_shapes[claim_key] != shape:
            raise ValueError(f"Provenance registry claim key `{claim_key}` is reused for a different subject, namespace, or field path.")
        claim_shapes[claim_key] = shape
        if "asserted_value" not in assertion:
            raise ValueError(f"Provenance registry `{context}.asserted_value` is required, including when null.")
        status = require_string(assertion, "assertion_status", context)
        validate_pack_values(schema_packs, "provenance.assertion-status", (status,), f"{context}.assertion_status")
        raw_links = assertion.get("evidence_links")
        if not isinstance(raw_links, list) or not raw_links:
            raise ValueError(f"Provenance registry `{context}.evidence_links` must be a non-empty list.")
        links: list[ProvenanceEvidenceLink] = []
        seen_sources: set[str] = set()
        for link_index, raw_link in enumerate(raw_links):
            link_context = f"{context}.evidence_links[{link_index}]"
            link = require_mapping(raw_link, link_context)
            assert_allowed_keys(
                link,
                {"source_id", "evidence_role", "locators"},
                f"Provenance registry `{link_context}`",
            )
            source_id = require_string(link, "source_id", link_context)
            if source_id not in sources.sources:
                raise ValueError(f"Provenance registry `{link_context}.source_id` references unknown source `{source_id}`.")
            if source_id in seen_sources:
                raise ValueError(f"Provenance registry `{context}.evidence_links` repeats source `{source_id}`.")
            seen_sources.add(source_id)
            role = require_string(link, "evidence_role", link_context)
            validate_pack_values(schema_packs, "provenance.evidence-role", (role,), f"{link_context}.evidence_role")
            raw_locators = link.get("locators")
            if not isinstance(raw_locators, list) or not raw_locators:
                raise ValueError(f"Provenance registry `{link_context}.locators` must be a non-empty list.")
            locators = tuple(
                parse_locator(raw_locator, f"{link_context}.locators[{locator_index}]", source_id, sources, schema_packs)
                for locator_index, raw_locator in enumerate(raw_locators)
            )
            for locator in locators:
                if locator.id in seen_locator_ids:
                    raise ValueError(f"Provenance registry evidence-locator ID `{locator.id}` is duplicated.")
                seen_locator_ids.add(locator.id)
            links.append(ProvenanceEvidenceLink(source_id, role, locators))
        roles = {link.evidence_role for link in links}
        if status in {"verified", "inferred"} and "supports" not in roles:
            raise ValueError(f"Provenance registry `{context}` status `{status}` requires supporting evidence.")
        if status == "disputed" and not {"supports", "contradicts"}.issubset(roles):
            raise ValueError(f"Provenance registry `{context}` disputed status requires supporting and contradicting evidence.")
        assertions.append(ProvenanceAssertion(
            assertion_id, claim_key, subject_type, subject_id, claim_namespace,
            field_path, assertion["asserted_value"], status,
            parse_temporal_window(assertion, "observed_at", context, schema_packs),
            parse_temporal_window(assertion, "effective_window", context, schema_packs),
            tuple(links),
        ))

    for scope in sources.applicability_scopes.values():
        if scope.target_type == "provenance-claim" and scope.target_id not in claim_shapes:
            raise ValueError(f"Provenance registry applicability scope `{scope.id}` references unknown provenance claim `{scope.target_id}`.")
    edges: dict[str, set[str]] = {}
    for item in supersessions:
        for claim_key in (item.source_claim_key, item.target_claim_key):
            if claim_key not in claim_shapes:
                raise ValueError(f"Provenance registry claim supersession `{item.id}` references unknown claim `{claim_key}`.")
        if claim_shapes[item.source_claim_key] != claim_shapes[item.target_claim_key]:
            raise ValueError(f"Provenance registry claim supersession `{item.id}` must relate claims with the same subject, namespace, and field path.")
        edges.setdefault(item.source_claim_key, set()).add(item.target_claim_key)
    visited: set[str] = set()
    active: set[str] = set()
    def visit(claim_key: str) -> None:
        if claim_key in active:
            raise ValueError(f"Provenance registry contains a claim-supersession cycle involving `{claim_key}`.")
        if claim_key in visited:
            return
        active.add(claim_key)
        for target in edges.get(claim_key, set()):
            visit(target)
        active.remove(claim_key)
        visited.add(claim_key)
    for claim_key in edges:
        visit(claim_key)

    return ProvenanceRegistry(
        project.provenance_registry, schema_version, tuple(assertions),
        tuple(supersessions), sources, entities, reconciliations
    )
