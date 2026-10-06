"""Git comparison and coherent content snapshots for explain-only CI selection."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid

MODES = {"committed", "hosted-pr", "hosted-commit", "local-staged", "local-worktree", "full"}
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
REGULAR = {"100644", "100755"}
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024


class ScopeError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ScopeError(message)


def safe_path(value):
    require(isinstance(value, str) and value and not value.startswith(("/", "\\")), "Unsafe repository path")
    require("\\" not in value and ":" not in value and "\0" not in value, f"Unsafe repository path: {value!r}")
    require(all(part not in ("", ".", "..", ".git") for part in value.split("/")), f"Unsafe repository path: {value!r}")
    return value


def decode(value):
    try:
        return value.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ScopeError("Unrepresentable UTF8 Git path data") from error


def nul_records(value):
    require(not value or value.endswith(b"\0"), "Truncated NUL-delimited Git data")
    return value[:-1].split(b"\0") if value else []


def parse_inventory(value, index=False):
    result = {}
    for record in nul_records(value):
        require(b"\t" in record, "Malformed Git inventory")
        header, raw_path = record.split(b"\t", 1)
        fields = decode(header).split(" ")
        require(len(fields) == 3, "Malformed Git inventory header")
        mode, second, third = fields
        oid = second if index else third
        require(OID.fullmatch(oid), "Malformed inventory object ID")
        require(third == "0" if index else second == "blob", "Unmerged index or unsupported tree object")
        path = safe_path(decode(raw_path))
        require(path not in result, "Duplicate Git inventory path")
        result[path] = {"mode": mode, "oid": oid}
    return result


def parse_diff(value):
    tokens = nul_records(value)
    result = []
    index = 0
    while index < len(tokens):
        header = decode(tokens[index])
        index += 1
        require(header.startswith(":"), "Malformed raw diff header")
        fields = header[1:].split(" ")
        require(len(fields) == 5, "Malformed raw diff fields")
        old_mode, new_mode, old_oid, new_oid, status = fields
        require(OID.fullmatch(old_oid) and OID.fullmatch(new_oid), "Malformed raw diff object ID")
        require(re.fullmatch(r"[A-Z](?:[0-9]{1,3})?", status), "Unsupported raw diff status")
        count = 2 if status[0] in ("R", "C") else 1
        require(status[0] not in "RC" or (status[1:].isdigit() and int(status[1:]) <= 100), "Invalid rename/copy score")
        require(index + count <= len(tokens), "Truncated rename/copy path pair")
        paths = [safe_path(decode(item)) for item in tokens[index : index + count]]
        index += count
        result.append(
            {
                "status": status,
                "old_path": paths[0] if status[0] != "A" else None,
                "new_path": paths[-1] if status[0] != "D" else None,
                "old_mode": old_mode,
                "new_mode": new_mode,
            }
        )
    return result


class Git:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.environment = os.environ.copy()
        for name in list(self.environment):
            if name.startswith("GIT_"):
                self.environment.pop(name)
        self.environment.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat")

    def read(self, *arguments, input_data=None):
        command = ["git", "-c", "core.fsmonitor=false", "-c", "core.untrackedCache=false", *arguments]
        try:
            result = subprocess.run(
                command,
                cwd=self.root,
                env=self.environment,
                input=input_data,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ScopeError(f"Git read unavailable: {error}") from error
        require(result.returncode == 0, "Git read failed: " + result.stderr.decode("utf-8", errors="replace").strip())
        return result.stdout

    def resolve(self, reference):
        require(
            isinstance(reference, str) and reference.strip() == reference and reference,
            "Explicit Git reference required",
        )
        value = decode(self.read("rev-parse", "--verify", "--end-of-options", reference + "^{commit}")).strip()
        require(OID.fullmatch(value), "Invalid resolved commit ID")
        return value

    def index(self):
        return self.read("ls-files", "--stage", "-z")

    def blobs(self, inventory):
        ids = list(dict.fromkeys(row["oid"] for row in inventory.values()))
        if not ids:
            return {}
        request = ("\n".join(ids) + "\n").encode("ascii")
        sizes = self.read("cat-file", "--batch-check", input_data=request).splitlines()
        require(len(sizes) == len(ids), "Missing blob size inventory")
        total = 0
        for oid, line in zip(ids, sizes):
            fields = decode(line).split(" ")
            require(len(fields) == 3 and fields[:2] == [oid, "blob"], "Unexpected size inventory")
            size = int(fields[2])
            total += size
            require(0 <= size <= MAX_FILE_BYTES and total <= MAX_SNAPSHOT_BYTES, "Snapshot byte allowance exceeded")
        raw = self.read("cat-file", "--batch", input_data=request)
        values, offset, total = {}, 0, 0
        for oid in ids:
            end = raw.find(b"\n", offset)
            require(end >= 0, "Truncated blob header")
            fields = decode(raw[offset:end]).split(" ")
            require(len(fields) == 3 and fields[:2] == [oid, "blob"], "Unexpected batch object")
            size = int(fields[2])
            total += size
            require(0 <= size <= MAX_FILE_BYTES and total <= MAX_SNAPSHOT_BYTES, "Snapshot byte allowance exceeded")
            start = end + 1
            require(raw[start + size : start + size + 1] == b"\n", "Truncated blob content")
            values[oid] = raw[start : start + size]
            offset = start + size + 1
        require(offset == len(raw), "Unexpected trailing blob data")
        return values


class Snapshot:
    def __init__(self, files, modes, windows=False):
        require(set(files) == set(modes), "Snapshot inventory mismatch")
        require(
            sum(len(content) for content in files.values()) <= MAX_SNAPSHOT_BYTES, "Snapshot byte allowance exceeded"
        )
        seen = set()
        for path in files:
            safe_path(path)
            require(modes[path] in REGULAR, f"Unsupported snapshot file mode: {path}")
            if windows:
                require(path.casefold() not in seen, "Ambiguous Windows path collision")
                seen.add(path.casefold())
        self.files = files
        self.modes = modes
        self.manifest = [
            {
                "path": path,
                "mode": modes[path],
                "sha256": hashlib.sha256(files[path]).hexdigest(),
                "bytes": len(files[path]),
            }
            for path in sorted(files)
        ]
        encoded = json.dumps(self.manifest, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.digest = hashlib.sha256(encoded).hexdigest()

    def materialize(self, repository, parent):
        repository = Path(repository).resolve()
        owner = repository / ".tmp"
        parent = Path(parent)
        parent = (repository / parent).resolve()
        require(owner.resolve() == owner and parent.is_relative_to(owner), "Snapshot output escapes owned .tmp")
        try:
            Git(repository).read(
                "check-ignore",
                "--no-index",
                "--stdin",
                "-z",
                input_data=(parent.relative_to(repository).as_posix() + "/\0").encode("utf-8"),
            )
        except ScopeError as error:
            raise ScopeError("Snapshot output must be Git-ignored owned .tmp storage") from error
        parent.mkdir(parents=True, exist_ok=True)
        destination = parent / ("snapshot-" + uuid.uuid4().hex)
        destination.mkdir()
        for path in sorted(self.files):
            target = destination / path
            require(target.resolve().is_relative_to(destination), "Snapshot target escape")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(self.files[path])
            if os.name != "nt" and self.modes[path] == "100755":
                target.chmod(0o755)
        self.verify(destination)
        return destination

    def verify(self, destination):
        destination = Path(destination).resolve()
        found = set()
        for directory, folders, filenames in os.walk(destination, followlinks=False):
            for name in folders + filenames:
                path = Path(directory) / name
                require(
                    not path.is_symlink() and not path.is_junction() and path.resolve().is_relative_to(destination),
                    "Materialized snapshot link escape",
                )
            found.update((Path(directory) / name).relative_to(destination).as_posix() for name in filenames)
        require(found == set(self.files), "Materialized snapshot inventory drift")
        for path, content in self.files.items():
            target = destination / path
            require(
                not target.is_symlink() and target.resolve().is_relative_to(destination),
                "Materialized snapshot link escape",
            )
            require(target.read_bytes() == content, "Materialized snapshot content drift")


def snapshot_from_git(git, inventory, windows):
    for path, row in inventory.items():
        require(row["mode"] in REGULAR, f"Unsupported symlink/gitlink snapshot entry: {path}")
    blobs = git.blobs(inventory)
    return Snapshot(
        {path: blobs[row["oid"]] for path, row in inventory.items()},
        {path: row["mode"] for path, row in inventory.items()},
        windows,
    )


def worktree_snapshot(git, windows):
    index_bytes = git.index()
    inventory = parse_inventory(index_bytes, index=True)
    untracked = git.read("ls-files", "--others", "--exclude-standard", "-z")
    paths = set(inventory) | {safe_path(decode(path)) for path in nul_records(untracked)}
    files, modes, total = {}, {}, 0
    for path in sorted(paths):
        target = git.root / path
        if not target.exists() and not target.is_symlink():
            continue
        require(
            not target.is_symlink() and target.resolve().is_relative_to(git.root),
            f"Worktree link escape/unsupported link: {path}",
        )
        info = target.stat()
        require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_FILE_BYTES, f"Unsupported worktree entry: {path}")
        require(path not in inventory or inventory[path]["mode"] in REGULAR, f"Unsupported gitlink/symlink: {path}")
        content = target.read_bytes()
        require(
            len(content) <= MAX_FILE_BYTES and target.stat().st_mtime_ns == info.st_mtime_ns,
            "Worktree size/content drift",
        )
        total += len(content)
        require(total <= MAX_SNAPSHOT_BYTES, "Snapshot byte allowance exceeded")
        files[path] = content
        modes[path] = (
            ("100755" if info.st_mode & stat.S_IXUSR else "100644")
            if os.name != "nt"
            else inventory[path]["mode"]
            if path in inventory
            else "100644"
        )
    require(
        index_bytes == git.index() and untracked == git.read("ls-files", "--others", "--exclude-standard", "-z"),
        "Index/untracked inventory drift",
    )
    for path, content in files.items():
        target = git.root / path
        require(not target.is_symlink() and target.resolve().is_relative_to(git.root), "Worktree link drift")
        require(target.read_bytes() == content, "Worktree content drift")
    return Snapshot(files, modes, windows), hashlib.sha256(index_bytes).hexdigest(), untracked


def resolve_scope(root, mode, base=None, source=None, executed=None, windows=None):
    require(mode in MODES, "Explicit supported scope mode required")
    git = Git(root)
    require(
        Path(decode(git.read("rev-parse", "--show-toplevel")).strip()).resolve() == git.root,
        "Scope root must be repository top level",
    )
    windows = os.name == "nt" if windows is None else windows
    head = git.resolve("HEAD")
    local = mode in {"local-staged", "local-worktree", "full"}
    require(
        not local or (base is None and source is None and executed is None),
        "Local/full scope cannot mix committed refs",
    )
    changes, fallback = [], []
    provenance = {
        "mode": mode,
        "base_tip": None,
        "source_tip": None,
        "merge_base": None,
        "executed_commit": head,
        "checkout_kind": "local-snapshot" if local else "source",
        "index_digest": None,
        "snapshot_kind": "worktree" if local else "commit",
    }
    if mode == "local-staged":
        index_bytes = git.index()
        snapshot = snapshot_from_git(git, parse_inventory(index_bytes, index=True), windows)
        require(index_bytes == git.index(), "Index drift during capture")
        provenance.update(base_tip=head, index_digest=hashlib.sha256(index_bytes).hexdigest(), snapshot_kind="index")
    elif local:
        snapshot, index_digest, untracked = worktree_snapshot(git, windows)
        provenance["index_digest"] = index_digest
        if mode != "full":
            provenance["base_tip"] = head
    else:
        require(
            base is not None and source is not None, "Committed/hosted scope requires explicit base and source refs"
        )
        source_tip = git.resolve(source)
        execution_tip = git.resolve(executed or "HEAD")
        require(execution_tip == head, "Executed ref must identify actual checkout HEAD")
        require(
            not git.read("status", "--porcelain=v1", "-z", "--untracked-files=all"),
            "Committed/hosted checkout is dirty",
        )
        require(mode == "hosted-pr" or execution_tip == source_tip, "Source and executed checkout disagree")
        snapshot = snapshot_from_git(git, parse_inventory(git.read("ls-tree", "-r", "-z", execution_tip)), windows)
        provenance.update(
            source_tip=source_tip,
            executed_commit=execution_tip,
            checkout_kind="source" if execution_tip == source_tip else "merge",
        )
        try:
            base_tip = git.resolve(base)
            provenance["base_tip"] = base_tip
            merge_base = decode(git.read("merge-base", base_tip, source_tip)).strip()
            require(OID.fullmatch(merge_base), "Indeterminate merge base")
            provenance["merge_base"] = merge_base
            if mode == "hosted-pr" and execution_tip != source_tip:
                parents = decode(git.read("show", "-s", "--format=%P", execution_tip)).strip().split()
                if parents != [base_tip, source_tip]:
                    fallback.append("merge execution cannot be bounded by exact target/source parents")
            if decode(git.read("rev-parse", "--is-shallow-repository")).strip() == "true":
                fallback.append("shallow history: comparison precision is not trusted")
        except ScopeError as error:
            fallback.append("comparison unavailable: " + str(error))
    try:
        if mode == "full":
            fallback.append("explicit full scope")
        elif mode == "local-staged":
            changes = parse_diff(
                git.read(
                    "diff",
                    "--cached",
                    "--raw",
                    "--no-abbrev",
                    "-z",
                    "-M",
                    "-C",
                    "--find-copies-harder",
                    "--no-ext-diff",
                    "--no-textconv",
                    head,
                    "--",
                )
            )
        elif mode == "local-worktree":
            changes = parse_diff(
                git.read(
                    "diff",
                    "--raw",
                    "--no-abbrev",
                    "-z",
                    "-M",
                    "-C",
                    "--find-copies-harder",
                    "--no-ext-diff",
                    "--no-textconv",
                    head,
                    "--",
                )
            )
            changes += [
                {
                    "status": "A",
                    "old_path": None,
                    "new_path": safe_path(decode(path)),
                    "old_mode": "000000",
                    "new_mode": snapshot.modes[safe_path(decode(path))],
                }
                for path in nul_records(untracked)
            ]
        elif provenance["merge_base"]:
            changes = parse_diff(
                git.read(
                    "diff",
                    "--raw",
                    "--no-abbrev",
                    "-z",
                    "-M",
                    "-C",
                    "--find-copies-harder",
                    "--no-ext-diff",
                    "--no-textconv",
                    provenance["merge_base"],
                    provenance["source_tip"],
                    "--",
                )
            )
    except ScopeError as error:
        changes = []
        fallback.append("comparison data unsafe/indeterminate: " + str(error))
    for change in changes:
        if change["status"][0] not in "AMDRCT" or "160000" in (change["old_mode"], change["new_mode"]):
            fallback.append("unsupported status/gitlink impact")
    require(git.resolve("HEAD") == head, "HEAD drift during resolution")
    if mode in {"local-worktree", "full"}:
        repeated, repeated_index, _ = worktree_snapshot(git, windows)
        require(
            repeated.digest == snapshot.digest and repeated_index == provenance["index_digest"],
            "Worktree/index drift during comparison",
        )
    elif mode == "local-staged":
        require(hashlib.sha256(git.index()).hexdigest() == provenance["index_digest"], "Index drift during comparison")
    if not local:
        require(git.resolve(source) == provenance["source_tip"], "Source ref drift")
        if provenance["base_tip"]:
            require(git.resolve(base) == provenance["base_tip"], "Base ref drift")
        require(not git.read("status", "--porcelain=v1", "-z", "--untracked-files=all"), "Checkout drift")
    provenance["snapshot_digest"] = snapshot.digest
    paths = sorted({path for change in changes for path in (change["old_path"], change["new_path"]) if path})
    report = {
        "contract": "ci-change-scope",
        "contract_version": 1,
        "status": "resolved",
        "provenance": provenance,
        "changes": changes,
        "fallback_reasons": list(dict.fromkeys(fallback)),
        "snapshot_manifest": snapshot.manifest,
        "policy_scope": {
            "mode": "full" if fallback else "changed",
            "paths": sorted(snapshot.files) if fallback else paths,
            "deletion_precision": "lost/not-compared" if fallback else "complete",
            "dispositions": [
                {
                    "path": path,
                    "status": "pending-validation" if path in snapshot.files else "pending-deletion-integrity",
                    "validated": False,
                }
                for path in (sorted(snapshot.files) if fallback else paths)
            ],
        },
        "materialized": False,
        "execution_ready": False,
    }
    return report, snapshot
