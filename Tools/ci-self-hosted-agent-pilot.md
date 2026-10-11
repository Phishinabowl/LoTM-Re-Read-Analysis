# Bounded Windows Self-Hosted Agent Pilot

Status: preparation in progress; maintainer created the dedicated domain service account.
No agent installed or registered; further host provisioning remains subject to concrete review.
The approved agent/tool directories were created and their protected ACLs verified;
the service identity can modify the agent root and read/execute the separate admin-owned tool root.
The maintainer approved shared versioned tools for other development projects. `C:\DevTools`
was created with verified admin/SYSTEM write access and user/CI read-execute access. The earlier
KM-specific tool directory remains empty and is not the selected installation destination.
Shared Python 3.14.8 x64 was installed from the official installer after published SHA-256
and Authenticode publisher verification. Interpreter, standard library and disposable venv
checks passed; the installer left PATH unchanged. The maintainer subsequently authorized
appending the Python root and Scripts directories to system PATH for interactive development;
existing entries were preserved and fresh-process resolution verified. CI retains its explicit path.
PowerShell 7.6.6, Node 24.15.0 and npm 11.12.1
were verified by actual execution and can be reused. Service-identity execution remains pending.
Owner: [CI modernization Phase 6.5](ci-testing-modernization-plan.md#phase-65-host-equivalence-and-policy-adoption-review).
The implementation plan's current 6.5.1-6.5.6 checkpoints remain authoritative for sequencing
and acceptance; this document supplies pilot detail. This proposal does not close 6.5, adopt a backend,
change required checks, reopen PRs or activate content selection.

## Objective And Boundary

Evaluate one Windows self-hosted Azure Pipelines agent on an existing shared development VM
for the reusable knowledge-management (KM) platform. LoTM is its first consumer and proving
ground. New pilot infrastructure names use KM; existing repository paths and historical names
are not renamed by this increment.
Compare setup cost, required feedback time, execution minutes, reliability and maintenance with
the existing Microsoft-hosted path. Agent placement must preserve the repository's catalogs,
fixtures, process isolation, deadlines, exit behavior and admitted reports.

The maintainer prefers host reuse. The inspected Windows Server 2019 guest has four vCPUs,
16 GiB RAM and approximately 57 GiB free system-disk space. These are initial observations,
not a workload benchmark or a reason to increase resources before measurement. Existing
application services remain running despite inactive upstream lab use. Their credentials,
configuration and permissions must remain separate from CI.

No current VM backup is available. The maintainer explicitly accepts the risk of rebuilding
the shared development VM if its base disks or storage are lost or damaged. The approved
pilot recovery approach is a short-lived pre-installation snapshot; independent backup/export
is deferred. The maintainer reports the pre-installation snapshot was created and the guest
powered on again; existing strict-host-checked SSH access was verified afterward. Snapshot
creation time and the 72-hour cleanup deadline are recorded in ignored private evidence.
The snapshot task/entry was not independently inspected and reversion has not been tested.
The maintainer subsequently installed Windows updates and rebooted the guest; existing SSH/admin
access and account SID resolution were verified and queried pending-reboot markers were absent.
Reverting the snapshot would undo those guest updates; the separately created domain account
is not removed by VM reversion. No independent patch-currency audit is claimed.
Private host/account/network details stay in existing private connection configuration and
ignored inspection evidence, not this shared document.

## 1. Preparation And Approval

### 1.1 Recovery And Host Readiness

- Before installation, prepare one short-lived pre-installation VM snapshot. Inspect existing
  snapshots and available datastore space first; guest free disk space is not datastore headroom.
  Preserve unrelated snapshots. Confirm the snapshot covers the intended virtual disks.
- For this inactive lab workload, prefer a graceful guest shutdown, a powered-off disk snapshot
  without memory capture, and normal power-on afterward. Confirm task success, the snapshot
  entry/time and existing SSH access before installing anything. No tested reversion is claimed.
- Record the actual creation time and a cleanup deadline no later than 72 hours afterward.
  Review sooner if datastore use grows substantially. After accepting the changed state, delete
  the pilot snapshot through the supported UI and let consolidation finish; deletion retains
  current changes, whereas reversion discards changes made since the snapshot.
- If verification is unfinished at the deadline, pause further installation and review whether
  to retain the current state or revert. Do not automatically revert shared application state,
  indefinitely extend retention or delete underlying snapshot files manually.
- Review OS patch currency and the host's maintenance window. No unattended update/reboot,
  application removal or hypervisor resource change is implied beyond the reviewed snapshot
  shutdown/power-on window.
- The snapshot depends on the original disks and is not a backup or protection against datastore
  failure. Independent backup and longer-term recovery remain a deferred operational follow-up.
  Snapshot rollback affects all guest changes, but does not undo ADO pool/agent registrations.

### 1.2 Concrete Access And Provisioning Review

- Existing administrative SSH access is functional and host identity is verified. Reuse it
  for approved preparation; do not create another SSH key or duplicate connection profile.
- No CI-specific local account, agent service or candidate workspace was found during inspection.
  The maintainer requests a domain service identity. Propose one dedicated non-admin domain
  account, `svc_km_ci`, for this agent. The maintainer checked the directory, created the account
  in the selected service-account OU, and verified it is enabled, has password expiration enabled,
  and belongs only to Domain Users. The updated pilot host resolves its SID. Domain membership
  does not imply a need for domain resource permissions. VM reversion does not remove this account.
- Propose a dedicated pool, `KM-CI-Pilot`, associated only with this project and explicitly
  authorized only for the pilot pipeline. Do not enable access for all pipelines or reuse the
  unrestricted shared Default pool as a shortcut.
- Before changing anything, review account creation, service-logon rights, folder ACLs, pool
  permissions, registration authentication, exact software artifacts and installation paths.
  User approval covers that concrete increment, not unrelated access changes.
- The agent identity is not added to Administrators, domain administration, MID accounts or
  administrative SSH groups. Registration permissions and the service identity are separate.
  Grant service-logon rights only on the pilot host and the reviewed filesystem permissions;
  inspect effective domain policy before applying local rights. Credential lifetime/rotation
  is an explicit operating responsibility; do not silently disable password expiration.
- Prefer a supported interactive registration method if available; inspect existing authorized
  methods first. Any new registration credential needs explicit approval. Never print/store its
  value in repository files, scripts, command-line logs or evidence. Service credentials use the
  operating system and supported agent setup, not a repository-managed password file.

**Checkpoint:** recovery disposition and concrete machine/access changes are reviewed before execution.

## 2. Supported Provisioning And Registration

### 2.1 Provision Only Initial Prerequisites

- Agent root: `C:\agents\km-ci`; work directory beneath that root. Shared versioned
  tool root: `C:\DevTools`. Use version-specific subdirectories, explicit selected executables,
  and no global PATH replacement by default. Inspect existing tools first and preserve other applications.
- Admin-owned tools are readable/executable but not writable by the agent. Agent workspace,
  environment and dependency-cache locations are writable by its identity and administrators.
  Verify actual ACLs, including separation from existing application configuration.
- Select the Windows x64 agent package offered by ADO and verify its supported OS/runtime
  requirements, publisher/version and available integrity evidence before installation. Agent
  security/service updates remain an operating responsibility, not a permanent frozen version.
- Provision ordinary x64 CPython 3.14.8 once through a supported official installation method.
  Use the repository's existing pip/dependency lock and environment verification. Do not recreate
  installed-runtime transport, release-inventory sealing or custom restore controllers.
  The approved shared installation is `C:\DevTools\Python\3.14.8\python.exe`, installed
  for all users with the traditional installer; no launcher or file-association changes.
  A separately approved system PATH update makes this default interpreter available by name;
  CI continues selecting the explicit versioned executable.
  Its bundled pip is 26.2.1; preserve that shared baseline and pin pip 26.2 inside the KM environment.
- `UsePythonVersion@0` cannot download Python on self-hosted agents. Either provision its documented
  tool-cache layout and disable registry downloading, or use the verified explicit interpreter path.
  Choose and qualify one small approach before wiring; never mark an incomplete runtime as complete.
- Preserve global application tools. Post-update inspection reports installed PS7 7.6.6 and
  Node 24.15.0, matching the pinned versions; qualify actual runtime behavior before deciding
  whether another installation is necessary. Pester 6.2.0 and other dependencies use existing owned caches.
- Python packages such as pytest, PyYAML and Pillow belong in project-owned virtual environments,
  using the applicable dependency locks. Share downloaded dependency payloads only through reviewed
  cache permissions; do not give multiple project identities unrestricted write access to a trusted cache.
  Standalone tools such as actionlint can be reused from admin-owned versioned directories.
- Initial execution needs core Python/PowerShell test dependencies, not build/render tooling.
  Existing application Chrome is not the repository's pinned renderer and must not be substituted.
- Verify outbound HTTPS under the eventual service identity, not just the administrative session.
  No broad new inbound listener is required for agent job dispatch. Network segmentation, pool
  permissions and accessible host services remain part of the shared-host trust boundary.

### 2.2 Register One Agent

- Concrete proposed registration checkpoint: create one self-hosted organization pool
  `KM-CI-Pilot`, with automatic provisioning to all projects disabled. Associate its queue only
  with this project, and leave open access to all pipelines disabled. Authorize only the eventual
  reviewed manual pilot pipeline; no existing pipeline is redirected by creating this pool.
- Select the Windows x64 package offered by this organization's New agent dialog and verify its
  version, download origin, integrity evidence and supported Server 2019 requirements before
  execution. Extract only into the prepared empty `C:\agents\km-ci` root.
- Register one agent named `KM-CI-01` with interactive `config.cmd`, using `AAD` device-code
  authentication and the maintainer's existing authorized ADO login. The maintainer completes
  browser sign-in and enters the domain service-account password locally at the masked prompt.
  Do not forward either password or registration tokens through the chat or orchestration tools.
- Configure service mode, not autologon, under the dedicated domain identity with `_work` under
  the agent root. Permit supported setup to grant that identity Log on as a service on this host;
  inspect effective policy first and stop for review if domain policy overrides the grant.
  No administrator membership, extra domain group, SSH access or general domain resource grant.
- Register one Windows agent as a service with the reviewed identity and pool permissions.
- Verify it is online, matches the required OS/tools and runs without administrative membership.
- Capture restart/reconnection behavior during an agreed maintenance window. Do not restart the
  VM or unrelated services to prove this checkpoint.
- Keep the pilot manually invoked, nonrequired and restricted to reviewed source. No external
  contribution builds execute on this persistent lab host.

**Checkpoint:** one correctly scoped agent is available; no paid capacity or default CI adoption.

## 3. Bounded Execution And Comparison

### 3.1 Identity, Access And Cleanup Smoke

- Verify real service identity and a non-admin token, pinned tool identity, private writable
  workspace, intended application-access separation, and source protection.
- Use synthetic files to prove workspace cleanup; do not probe real credentials or modify MID
  files. Review effective ACLs for protected application paths.
- Provision reusable tools once, retain verified dependency payloads, and create clean execution
  environments/source snapshots through existing runners. Persistence must not hide undeclared inputs.
- Bound captured diagnostics and artifact retention. Do not export credentials, personal network
  configuration, agent registration state or unrelated application data.

### 3.2 Small Existing Native Profile

- Begin with registered bootstrap/dependency tests and a small approved Windows conformance group.
  Reuse existing adapters and result admission; do not invent duplicate agent-specific test suites.
- Qualify one deterministic synthetic failure and cancellation with the existing process fixtures;
  avoid interrupting the host, MID or other application services.
- Verify failures remain visible, later independent work continues as required, descendants clean up,
  and the service remains available. Native and Markdown evidence must preserve actual coverage.

### 3.3 Same-Source Timing Screen

- Compare one managed reference with first-preparation and repeat-preparation lab runs at the same
  source, logical coverage, pins and fault-free mode. Reuse adequate managed evidence where valid.
- Initial hosted execution allowance is at most six deliberately queued jobs across smoke,
  comparison and failure/cancellation checks. Reconcile job count before queuing; failures are
  not permission for indefinite retries. Review any expansion before allocation.
- Record queue, preparation, workload, publication, total job seconds and resource samples separately.
  Distinguish first provisioning, retained-cache reuse and clean environment recreation.
- Report missing coverage honestly. These bounded runs are not full-profile, content-selection,
  PR merge-context, Windows/Linux parity or ordinary-backend adoption proof.

**Decision:** adopt only for a further scoped qualification if setup/feedback benefits justify
maintenance and shared-host exposure. Otherwise disable/unregister the pilot while preserving evidence.
No numerical speedup is promised. Routine feature/content goals remain owned by the modernization plan.

## 4. Later Decisions And Rollback

- Leave one free self-hosted slot and the existing hosted allocation unchanged initially.
  Mixed-pool concurrent execution needs explicit routing and matrix qualification; no second VM,
  $15 additional self-hosted slot or $80 hosted trial is purchased by this proposal.
- A broader accepted pilot can next qualify role-specific placement and the complete Windows
  obligations, with Linux retained on an approved execution host. Required gates remain intact.
- Content classification/minimal preparation is a separate applicability decision; faster agents
  must not become a reason to run the full framework portfolio for every content edit.
- Review after the bounded screen and again after approximately one month if operation continues.
  Record operational effort and keep/stop criteria; a review date is not an automatic cancellation.
- Stop using the pilot by disabling its pipeline/pool authorization and stopping/unregistering only
  its agent service. Preserve reports. Remove only pilot-owned paths/accounts after checking consumers;
  do not delete shared tools, SSH keys, application services or GPO links as CI cleanup.
- Existing managed execution remains the CI rollback path. Reverting the short-lived snapshot is
  a reviewed host rollback action because it also affects unrelated application state. After
  snapshot cleanup there is no independent VM backup; the accepted rebuild risk remains explicit.

## Official References

- [Windows Azure Pipelines agent setup](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/windows-agent?view=azure-devops)
- [Agent permissions and shared infrastructure](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)
- [Python selection on self-hosted agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0?view=azure-pipelines)
- [Parallel-job capacity](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops)
- [VMware snapshot limitations](https://knowledge.broadcom.com/external/article/318825/best-practices-for-using-vmware-snapshots.html)
