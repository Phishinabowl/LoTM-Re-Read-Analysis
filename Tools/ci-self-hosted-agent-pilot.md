# Bounded Windows Self-Hosted Agent Pilot

Status: 6.5.3 preparation and registration confirmed; bounded workload qualification remains pending.
The approved Windows x64 agent is registered and online. Its service runs under the dedicated
identity with no Administrators SID in the running token. Service restart/reconnect is verified;
runtime/dependency execution under that identity passes in the single manual preparation smoke.
The maintainer confirmed 6.5.3 closeout on 2026-10-11; further pilot obligations remain open.
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
were verified by actual execution and can be reused. Dependency/tool execution as the service identity
is now verified separately by the manual preparation-only job; administrative setup alone was not substituted.
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

**6.5.3 preparation evidence (2026-10-11, in progress):** The maintainer authorized this checkpoint.
`KM-CI-Pilot` was created as a self-hosted pool with cross-project auto-provisioning disabled;
its queue is associated only with the current project and has no authorized pipelines. The public
permission API returns no all-pipeline grant (null) and an empty pipeline list, including after the
explicit closed-access update. This is not yet proof of the final manual pipeline's authorization.
The organization offered Windows x64 agent 5.280.0. Its archive matches the organization-provided
SHA-256 and Agent.Listener has a valid Microsoft publisher signature; actual `--version` passes.
Microsoft's agent 5 documentation explicitly includes Windows Server 2019 and bundled .NET 10.
The prepared root was empty before extraction, no prior agent service was found, and effective
service-logon policy has no returned deny-service-logon entry. Supported setup still needs to add
the dedicated identity's service right and prove its resulting access. A project checkout at the
confirmed planning commit `bbb9ab6` was prepared for the existing dependency bootstrap. Online
development preparation and a separate offline check pass, verifying Python 3.14.8, project-local
pip 26.2, pytest 9.1.1, PyYAML 6.0.3, Ruff 0.16.1 and declared support packages; PowerShell probes
verify Pester 6.2.0, PSScriptAnalyzer 1.25.0 and powershell-yaml 0.4.12 from the owned module cache.
Shared Python's bundled pip remains unchanged. Build/media/render and actionlint acquisition were
not requested by this small-profile preparation. No ADO job is queued.

The maintainer completes the supported interactive configuration in an elevated Windows PowerShell
window on the pilot host. Registration uses `AAD`, the existing organization login, pool
`KM-CI-Pilot`, agent name `KM-CI-01`, service mode and `_work`. The domain service identity/password
are supplied locally; never include the password in command arguments or captured chat output.
Dependency/tool execution under the service identity remains open until verified.
The detached preparation attempt produced
no completion evidence; the bounded foreground preparation and independent offline check provide
the successful dependency proof. Neither preparation timing nor metadata-only pool setup is hosted
workload-performance evidence.

**Registration verification (2026-10-11):** The maintainer completed device-code registration and
local password entry, selected unrestricted service SID mode, and initially prevented service
startup. The final effective service-logon right includes the CI identity and preserves existing
grants. Setup's rights-enumeration warning occurred before that grant; subsequent Windows service
startup succeeds with exit code zero. The service was started after configuration review and ADO
reports the expected enabled agent online. Read-only process-token inspection verifies the intended
identity and absence of the Administrators SID. Unrestricted service SID mode is not administrator
membership. Setup added an agent-folder access group containing only the CI identity, without adding
it to Administrators. Queue access remains closed with no authorized pipelines. No workload job has
run and no service-account dependency or performance result is claimed.

**Reconnect and service-smoke wiring (2026-10-11):** The maintainer authorized reconnect and
service-account verification. Only the pilot service was restarted; a changed process ID, Running
state, exit code zero and ADO online state were observed. No host reboot or unrelated service restart
was used. The [manual service preparation pipeline](../.azuredevops/ci-self-hosted-pilot.yml) is
prepared locally, not published or registered. Its one Windows job counts toward the initial six-job
allowance when queued. Manual reason, the modernization branch, restricted pool and exact agent
are required; it does not change ordinary CI, schedule runs or accept external contributions.
Checkout credentials are not persisted. It checks the current job's non-admin service identity,
exact dispatched checkout, pinned shared runtime execution, denied shared-tool writes and synthetic
workspace cleanup, then uses the existing development bootstrap and independent offline verification
in the actual checkout's owned environment/module cache. Build/render/media tools are outside this
preparation-only job. Native framework units are explicitly zero; no full-profile pass is claimed.
Artifacts contain only preparation evidence, not a full environment or credential dump. Local YAML
structure/restriction checks and both PowerShell AST parses pass; final Azure compilation and actual
service-account checks await reviewed publication, definition creation and single-pipeline authorization.

## 3. Bounded Execution And Comparison

### 6.5.3 Service Preparation Acceptance Evidence

The three-file wiring checkpoint is confirmed and dual-published as `d83d2f3`; GitHub, Azure,
HEAD and upstream agree. Pipeline **KM CI Agent Pilot** is created without an automatic first run,
uses the dedicated pool/project queue, and is the only pipeline granted queue access. Generated
CI-trigger metadata on the new definition was explicitly cleared; revision 2 reads back with no
triggers, and its run inventory contains only the one manual run. The YAML disables push/PR
triggers and restricts execution to manual dispatch on the modernization branch and exact agent.
Azure preview compiled the one-job graph without workload execution. The separately authorized
[Azure run 78](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=78)
passes its single job on `KM-CI-01` at exact source `d83d2f3bbace50248e45bbdb891855485f3827af`.

Downloaded artifacts independently verify the dedicated non-admin service identity, denied writes
to the shared admin-owned tool root, synthetic temporary-workspace cleanup, exact shared Python/
PowerShell/Node/npm versions, project-local package/module pins and origins, and independent offline
dependency verification. The agent remains online afterward, and a post-run permission read confirms
only the pilot pipeline is authorized. No credentials or complete environment dump were published.
The service job's real checkout/environment is separate from the earlier administrative preparation
checkout; its actual under-account proof provides acceptance rather than relying on that setup probe.

| Observed segment | Seconds | Scope |
| --- | ---: | --- |
| Queue to run start | 3.396 | One observed dispatch |
| Run start to finish | 84.318 | Includes orchestration overhead |
| Queue to finish | 87.714 | Whole observed run |
| Physical job | 74.203 | Checkout, identity, dependencies and publication |
| First development bootstrap | 44.298 | Reported bootstrap elapsed |
| Independent offline check | 5.374 | Reported check elapsed |

These are preparation-smoke timings, not a framework suite, full-profile or same-source hosted/lab
performance comparison. The report explicitly records **zero framework units**, preparation-only
mode and no full-profile acceptance. This consumes **one of six** deliberately queued pilot jobs;
five remain for reviewed coverage/failure/cancellation/comparison obligations. No retry or additional
workload job was launched. Native profile, failure/cancellation, timing comparison and adopt-or-stop
remain 6.5.4/6.5.5; full/event/policy equivalence remains 6.5.6. The maintainer confirmed this evidence
and 6.5.3 closeout on 2026-10-11. No additional pilot job is authorized or queued by this closeout.

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
- [Agent 5 supported operating systems and bundled runtime](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/v5-agent?view=azure-devops)
- [Device-code registration](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/device-code-flow-agent-registration?view=azure-devops)
- [Agent permissions and shared infrastructure](https://learn.microsoft.com/en-us/azure/devops/pipelines/security/misc?view=azure-devops)
- [Python selection on self-hosted agents](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0?view=azure-pipelines)
- [Parallel-job capacity](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops)
- [VMware snapshot limitations](https://knowledge.broadcom.com/external/article/318825/best-practices-for-using-vmware-snapshots.html)
