# CI 6.1 Repository Synchronization And Host Readiness

**Status:** Readiness inspection and first cache pilot confirmed for publication on 2026-10-06,
based on `507caa4bea5743c3dad91bd077eedeb4f63d0d8f`. The maintainer authorizes continuing the hosted
portion after dual-host publication; this confirmation does not close 6.1.
**6.1 remains open:** no new hosted pilot has run, no ADO pipeline has been created, and no PR or
branch-policy change has been made. [The plan](ci-testing-modernization-plan.md#phase-61-repository-synchronization-and-host-readiness)
owns completion; [the integration design](ci-testing-host-integration-design.md) retains merge/event
authority. This record supplements its dated inspection rather than rewriting historical evidence.

## Verified Entry And Synchronization

The expanded Phase 5 gate was confirmed and published as `507caa4`. Its accepted
[77-unit OS comparison](ci-testing-os-comparison.md), semantic portfolio, source guards, local recipes
and provisional Windows full placement are the entry baseline. Linux eligibility and required Windows
image coverage remain; actual host costs can change placement at 6.5. Native/full goals remain 90/960
seconds with Phase 8.1 follow-up. Local WSL timing does not establish real agent speed.

Live `git ls-remote --heads` queries returned the same tips on GitHub and ADO:

| Ref | Identical commit |
| --- | --- |
| `main` | `608e48939ec352876ae919213a236592f46d982c` |
| `architecture/framework-extraction-foundation` | `c4b79326e8dde5420f61d318f4f541e752b6030a` |
| `architecture/ci-testing-modernization` | `507caa4bea5743c3dad91bd077eedeb4f63d0d8f` |

The checkout started clean on the modernization branch. `origin` fetches GitHub and retains exactly
two intended push URLs; `ado` fetches Azure Repos independently. Branch names map one-for-one.
Routine confirmed publication remains `git push origin HEAD`, followed by independent fetch/parity
checks. No extra refs, tags, force pushes or mirror publication are introduced.

GitHub is the sole merge authority. Synchronizing a future accepted framework merge is an explicitly
scoped target-ref operation; routine current-branch authorization does not grant that publication.
ADO validation PRs cannot create independent merge history.

| Publication observation | Safe response |
| --- | --- |
| HEAD/upstream/live GitHub/live ADO equal | Publication verified; do not push a second time. |
| One destination rejects or cannot be reached | Record the successful destination and failure; refresh both before retrying. A missing read is unknown, not an equal tip. |
| One destination is an ancestor of the intended commit | Verify ancestry and intended branch. A reviewed retry of the current dual push can bring the lagging destination forward; the already-current side is a no-op. |
| Either destination diverges or is ahead unexpectedly | Stop publication, inspect history and obtain a concrete recovery decision. Never force, merge in ADO, or overwrite history to hide divergence. |

These are reviewed recovery rules, not a claim that a destructive hosted divergence drill ran.
The confirmation publication will exercise the ordinary parity path; partial-failure recovery proof
must still be recorded before this 6.1 checklist item closes.

## Current Host Configuration

Successful authenticated API reads prove the following current scope. Credentials and personal
identity details are excluded from tracked evidence. No tokens are printed, saved or put in caches.

| Surface | 2026-10-06 inspection |
| --- | --- |
| GitHub repository | Public, enabled, default `main`; caller repository role `admin`. |
| GitHub Actions | Enabled; allowed actions `all`; host SHA-pinning enforcement disabled. Repository adapters still pin every adopted action to an immutable commit. |
| GitHub workflow token defaults | Read-only; workflow PR approvals disabled. Pilot requests only `contents: read`. |
| GitHub protections | Rulesets empty; `main` and framework target unprotected. Preserve existing check names; do not treat this as permission to install enforcement early. |
| Existing GitHub workflows | `CI` and `Work Annotation Policy` active. Two active caches total 29,654,461 bytes; this is inventory, not a measured transport benefit. |
| Azure repository | Private project/repository `LoTM Inspired KM Platform`, enabled, default `refs/heads/main`; original project/repository IDs unchanged. |
| ADO pipelines / policies / active PRs | All three inspected inventories empty. No working pipeline identity/agent allocation or per-pipeline permission is claimed. |
| ADO hosted queue | Queue 39, pool 9, nonlegacy `Azure Pipelines`; all-pipelines queue authorization enabled. This is the existing setting, not a new broad grant. |
| Private hosted entitlement | One free slot, zero purchased, 1,800 monthly minutes; build hub confirms one free/total hosted license and no provider discovery failure. |
| Private self-hosted entitlement | One free slot; Default pool has zero agents. No local/self-hosted agent is installed. |
| ADO retention | Runs/artifacts 30 days, PR runs 10 days, three retained runs per protected branch. |

The free private hosted job ceiling is 60 minutes; organization concurrency/minutes are shared with
other projects. Pilot jobs reserve 20 minutes and serialize ADO matrix legs. The hub reports zero
used minutes, which does not independently certify the exact remaining monthly balance. No capacity
purchase, subscription deployment or billing change is proposed.
[Microsoft parallel-job guidance](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops).

Inspection used the existing `gh`/Azure CLI authentication. Successful read and Git transport do not
prove every future pipeline-creation/build-policy permission. Verify the actual created pipeline's
execution identity during activation, and keep policy adoption at 6.3/6.5. The first hub-license
query used the wrong query-parameter route and returned 404; the correct `hubName=build` route succeeded.

## Staged Payload Transport Pilot

[Repository helper](CI/host_cache.py), [GitHub pilot](../.github/workflows/ci-cache-pilot.yml) and
[ADO pilot](../.azuredevops/ci-cache-pilot.yml) form a temporary setup experiment. They do not invoke
profiles, select tests, replace required checks, enable schedules or change any validation semantics.
Original CI remains in place. Retire the pilot after its measured transport is adopted into 6.2/6.3.

The first payload covers Python development/media wheels and PowerShell development modules.
Cache `.local/ci-cache` only; fresh pilot agents populate only those selected payloads. Python virtual
environments, source trees, reports, Git credentials, portable PS installations and build artifacts
are excluded. Node/npm/browser and build dependency transport remain explicit follow-up experiments
within 6.1; this initial payload does not claim them measured.

The repository-owned key hashes exact current runtime declarations, Python wheel lock, all root
requirements, npm lock/declarations and bootstrap/import/install helpers. It separates Windows/Linux
and x64, with a bounded operator namespace for controlled invalidation/recovery. No broad restore
prefix can cross lock or OS boundaries. Namespace is not a package-version authority.

GitHub uses separately pinned cache restore/save actions; ADO uses native `Cache@2`. Both restore
before calling the same bootstrap. On a host-reported hit, bootstrap runs offline and verifies wheel
digests, PowerShell content receipts, exact imports and versions while creating a fresh Python
environment. A hit cannot skip verification or become evidence of a passing test. Failed setup
blocks saving new cache content. ADO performs its cache save as a post-job operation after success;
restore and save task durations must be measured separately.
[GitHub cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching),
[Azure cache behavior](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops).

Python setup is pinned to 3.14.5. The helper checks actual PowerShell and uses exact 7.6.6; if the agent
image differs, it acquires a portable copy under owned `.local/ci-tools` with SHA256 values taken
from the official [7.6.6 checksum manifest](https://github.com/PowerShell/PowerShell/releases/download/v7.6.6/hashes.sha256).
It performs no machine installation. Runtime acquisition cost remains visible rather than being
attributed to payload-cache restore. Portable-runtime reuse/cache admission needs its own proof if
measurements justify it; no prepared agent image or package feed is needed now.

The GitHub pilot initially runs only for changes to its helper/workflow on the modernization branch,
and supports manual dispatch. ADO YAML has no CI/PR/scheduled trigger and needs a separately created,
nonrequired pipeline using this branch/YAML. Neither adapter supplies a build-validation policy.
Diagnostics are retained after ordinary failures; GitHub artifacts request seven-day retention and
ADO uses its inspected run retention. Cancellation/publication and native Tests-tab acceptance remain
6.4. Cache restore/save time is read from native task logs, not fabricated inside the local helper.

## Local Verification And Remaining Evidence

Focused bootstrap regressions pass **26 cases on Windows and Linux**. Six new cases are registered
through the existing `python-bootstrap` group/file: stable/platform-separated keys, changed-input
invalidation, unsafe labels, corruption rejection and explicit verified recovery. No new group or
language-neutral conformance fixture is added. Linux uses the prepared native interpreter with the
source file mounted from Windows and synthetic fixtures under Linux temporary storage; these are
functional checks, not native-filesystem benchmark samples.

An actual local offline pilot created its dedicated fresh Python environment from existing verified
wheels and verified exact PS module imports. It passed; its local supplied hit flag demonstrates the
bootstrap path, **not a GitHub/ADO cache hit**. Evidence is ignored under `.tmp/ci-cache-pilot` and
the new environment is owned under `.local/ci-environments`; unrelated prepared environments remain.

Before closing 6.1:

1. Confirm/publish the staged files through the normal dual push and verify exact branch parity.
2. Create the nonrequired ADO cache-pilot pipeline at the published modernization ref; record its
   pipeline ID, actual permissions, queued source revision, agent OS/version and run URLs.
3. Run both OS legs on both hosts: fresh namespace with `expect=miss`, the same namespace/key with
   `expect=hit`, then a new namespace with `expect=miss`. Capture queue, runtime acquisition,
   payload acquisition, environment creation, verification, cache restore/save and diagnostic upload
   durations separately. A failed expected hit is a failed experiment, not a silent online fallback.
4. Demonstrate hosted corruption/missing-provenance refusal and explicit recovery using a new cache
   namespace/fresh owned workspace; preserve failure evidence. Do not delete arbitrary caches or
   repair cached bytes implicitly. Complete scoped partial-publication recovery proof.
5. Qualify remaining build/render payload transport and exact Node/npm/browser provisioning; recheck
   real agent fonts/shared libraries and browser isolation. Carry observed costs into 6.5 admission.
6. Open the authorized draft GitHub/framework-target and ADO validation PRs when PR shadow wiring
   needs them at 6.2/6.3; attach the GitHub PR and record both links. Never merge independently in ADO.

**Rollback:** Disable/remove only this optional pilot and its later-created pipeline. Preserve old
CI, required identities, shared branch history and unrelated caches. No adoption decision depends
on a hosted measurement that has not yet happened.

Staged verification: repository Ruff lint, both changed Python files' formatting, actionlint across
all workflows, annotation policy (22/22 fixtures, 478 files, zero findings), 101 relative file links,
pilot YAML/permission/pin/timeout invariants and `git diff --check` pass. These static checks do not
certify Azure server YAML compilation, successful agent allocation or cache transport performance.
