# Todo Tree And GitHub Working Convention

## Purpose

Use Todo Tree as a lightweight, implementation-facing intake and navigation layer for work discovered inside the repository. It preserves small follow-ups, known defects, open questions, explicit assumptions, intentional workarounds, review needs, and verification needs beside the exact source or contract they concern.

Todo Tree is not the universal project backlog. Durable work must move to the artifact that owns its scope:

- LoTM content and research planning belongs in `CURRENT_STATE.md`.
- Framework-version findings and recommendations belong in `Framework/framework_evolution.md`.
- Cross-cutting engineering work that needs durable public coordination belongs in GitHub Issues.
- Private untriaged ideas may begin in ignored `.local/` notes, but those notes are an inbox rather than an authoritative backlog.

This convention applies to human maintainers and approved coding agents.

## Eligible Surfaces

Use annotations on implementation-bearing surfaces:

- Python, PowerShell, and other executable source;
- YAML, TOML, and other configuration formats that support comments;
- framework contracts, architecture documents, testing contracts, and maintainer-facing Markdown; and
- a precise source location that remains useful after the current task or conversation ends.

Do not place Todo Tree annotations in reader-facing LoTM articles, investigations, boards, volume summaries, generated exports, canonical source material, or artwork assets. Use the owning content artifact instead. Never add comments to JSON or another format that does not support them merely to create an annotation.

The tracked `.vscode/settings.json` excludes reader-facing, generated, ignored, source-heavy, and work-annotation fixture trees from Todo Tree scanning. It also excludes this standards document so its examples do not appear as live work. Exclusion globs are passed directly to ripgrep using Todo Tree's documented default behavior. This configuration has been verified in both `workspace only` and `workspace and open files` modes, including while this excluded standards document is open.

Use Todo Tree's `workspace` scan mode, displayed as `Workspace and Open Files`, so eligible annotations in open implementation files remain visible while the exclusion policy suppresses ineligible surfaces. The tracked folder settings and the local VS Code workspace launcher must carry the same complete Todo Tree configuration because workspace-file settings take precedence when the repository is opened through that launcher.

## Annotation Format

Use this format:

```text
TAG (OWNER): TRACKING - concise source-local explanation
```

Tracking is optional while an item remains local:

```python
# TODO (OWNER): Extract repeated boundary filtering after the parser change.
# QUESTION (UNASSIGNED): Decide which pack owns participation constraints.
# HACK (OWNER): Preserve this order because the upstream renderer rejects equivalent reordered input.
```

Keep the indexed line concise, specific, and understandable without the originating conversation. Put necessary supporting context on indented continuation comments:

```python
# ASSUMPTION (OWNER): One occurrence cannot be revisited twice.
#   Validation target: future repeated-participation semantics.
```

Use ASCII punctuation in annotations. End complete statements with a period.

## Executable Enforcement

`Tools/Static/work-annotations.json` is the executable policy registry for supported tags, local owners, scannable file types, self-excluded reference/fixture paths, prohibited locations, and the file-size safety bound. Keep it synchronized with this standard and the tracked/local VS Code Todo Tree exclusions.

Run the canonical policy tool from any working directory:

```powershell
python Tools\Static\lint_work_annotations.py
python Tools\Static\lint_work_annotations.py --json
```

A normal run first executes every valid and invalid fixture in `Tools/Static/Fixtures/Work-Annotations/cases.json`, then scans Git's tracked-plus-nonignored-untracked inventory. Use `--fixtures-only` for policy development and repeat `--path` for focused diagnosis. The linter validates syntax, ownership state, GitHub issue/assignee URL consistency, ASCII text, terminal punctuation, and repository placement. It does not query GitHub or prove that an issue exists, is open, or has the mirrored assignment; verify live state separately before creating or changing a GitHub-linked annotation.

Reader-facing and generated trees remain excluded from Todo Tree for usability but are prohibited, not ignored, by the linter. A tracked annotation placed there therefore fails policy even though it does not clutter the editor tree. The standards document and deliberate fixture corpus are the only current self-exclusions.

## Supported Tags

- `TODO`: Small, source-local follow-up work.
- `FIXME`: Known incorrect, unsafe, or unreliable behavior.
- `QUESTION`: An unresolved requirement, ownership decision, or design choice.
- `ASSUMPTION`: A consciously unverified premise that currently constrains behavior or design. State the validation trigger or consequence when it is not obvious.
- `HACK`: An intentional temporary workaround. Explain why it exists.
- `REVIEW`: Source, a contract, or an interpretation that needs human judgment.
- `VERIFY`: Behavior or an assertion that needs explicit testing or confirmation.

Avoid additional tags unless a recurring need is not represented by this set and the repository standard is updated first.

When an assumption is disproven, resolve the dependent implementation or convert the annotation to `FIXME`. When it is verified and remains important, replace it with an ordinary explanatory comment or promote it into the owning contract instead of leaving a permanently open annotation.

## Local Ownership

Before GitHub promotion, use only these identity-neutral owners:

- `OWNER`: The repository owner is currently responsible.
- `UNASSIGNED`: No local owner has been selected.

Do not put a real name, private identity, or guessed public account in an annotation. Coding agents are not durable owners and must not assign work to themselves.

Examples:

```python
# TODO (OWNER): Consolidate repeated source-priority comparisons.
# REVIEW (UNASSIGNED): Confirm whether this capability belongs in core.
```

Todo Tree extracts the parenthesized value as a subtag so entries can be grouped by local ownership state or, after promotion, GitHub handle.

## Promotion To GitHub

Promote an annotation when it needs one or more of the following:

- durable public tracking beyond the current branch or task;
- prioritization, scheduling, release planning, or acceptance criteria;
- coordination among contributors;
- design discussion that has outgrown a source comment;
- user-facing, security, compatibility, data-integrity, or delivery impact; or
- work whose consequences make it unsafe to rely only on a local source annotation.

When promotion is agreed but the issue does not exist, retain the local owner and mark the tracking state:

```python
# FIXME (OWNER): [GH-PENDING] - Repository discovery fails outside the project root.
```

After the issue exists, use its number, full URL, and actual GitHub assignment. Replace the local owner with the exact public GitHub handle only when GitHub shows that assignment:

```python
# FIXME (@GitHubHandle): GH #<number> - Repository discovery fails outside the project root.
#   Issue: https://github.com/<owner>/<repository>/issues/<number>
#   Assignee: https://github.com/GitHubHandle
```

If the issue exists but is unassigned, retain `UNASSIGNED` and omit the assignee line:

```python
# FIXME (UNASSIGNED): GH #<number> - Repository discovery fails outside the project root.
#   Issue: https://github.com/<owner>/<repository>/issues/<number>
```

GitHub is authoritative after promotion. The annotation mirrors the issue's primary source-side assignee and precise implementation location. GitHub may have multiple assignees; the annotation names at most one primary owner. Update stale assignment or issue state when the mismatch is noticed.

Do not remove a GitHub-linked annotation unless the associated source work is complete, the source location no longer exists, or the maintainer explicitly requests removal. Closing an issue without resolving the source annotation requires reconciliation rather than silent deletion.

## GitHub Integration Boundary

Coding agents may identify promotion candidates and draft an issue title, description, acceptance criteria, labels, or comments from repository and conversation context.

Coding agents must not:

- invent, infer, or guess an issue number or GitHub handle;
- claim an issue exists or is assigned without verification;
- create, assign, close, or otherwise modify a GitHub Issue unless the maintainer explicitly requests that action; or
- treat a source annotation as more authoritative than the linked GitHub Issue after promotion.

Normal approved Git operations are separate from this restriction.

## Artifact Routing

Do not use an annotation to avoid updating the artifact that already owns the information:

- A planned page or research target goes to `CURRENT_STATE.md`.
- A framework pressure-test finding, accepted limitation, or next-version recommendation goes to `Framework/framework_evolution.md`.
- A permanent testing obligation goes to `Framework/testing_methodology.md` and its executable suite where applicable.
- A stable architectural rule goes to the owning framework or architecture contract.
- A code-local reminder, defect anchor, assumption, or verification need may remain in Todo Tree.

An item may have both an owning backlog record and a source annotation when the precise source location remains useful. Include the tracking reference so the relationship is explicit rather than duplicating disconnected prose.

## Coding-Agent Behavior

When Codex or another approved coding agent works in this repository:

- Use annotations only for durable information another human or agent will need after the current task.
- Do not add annotations for internal reasoning, every possible improvement, or work that should be completed in the current task.
- Use `QUESTION` instead of silently inventing an unresolved rule.
- Use `ASSUMPTION` when implementation proceeds under an unverified premise, and identify its validation target or consequence.
- Use `HACK` for an intentional workaround and explain why it is necessary.
- Route content, framework, testing, and engineering work to their authoritative artifacts.
- Recommend GitHub promotion when an item outgrows a source-local comment.
- Use `[GH-PENDING]` only after promotion has been agreed.
- Never expose a real name or private identity in an annotation.
- Report annotations added, changed, promoted, reconciled, or removed in the task summary.
- Review annotations touched by the task before declaring the work complete.

## Triage Workflow

Review Todo Tree periodically and before branch or pull-request closure:

1. Group entries by tag and owner.
2. Resolve small source-local work that belongs in the current change.
3. Assign or deliberately retain `UNASSIGNED` items.
4. Route content and framework findings to their authoritative repository artifacts.
5. Mark agreed GitHub promotions `[GH-PENDING]` until the issue exists.
6. After issue creation and assignment, add the issue number, full issue URL, public handle, and assignee profile URL.
7. Reconcile stale issue state or ownership.
8. Remove resolved annotations with the change that resolves them.

Framework-version implementation and pressure-test confirmation must also classify every annotation introduced or exposed by that version. A version finding cannot remain only in Todo Tree; it must be represented in the evolution record and permanent testing contract when applicable.

## Guiding Rule

Capture precisely, route deliberately, and track publicly only after promotion.

If an item mainly helps the next maintainer understand or revisit an exact implementation location, keep it in Todo Tree. If it affects project planning, framework evolution, testing obligations, or durable engineering coordination, update the authoritative artifact and retain only a useful linked source annotation.
