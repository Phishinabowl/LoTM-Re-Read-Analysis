"""Verify a run publication inventory or recover interrupted evidence without executing tests."""

import argparse
import json
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode = True

from execution_reports import recover, verify_publication, confined


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--recover", action="store_true")
    args = parser.parse_args()
    try:
        owner = Path(args.run).absolute()
        root = Path(args.root).absolute()
        if not owner.resolve().is_relative_to(root / ".tmp") or owner == root / ".tmp":
            raise ValueError("Report ownership requires a repository .tmp child")
        confined(owner, "events.jsonl")
        if args.recover:
            destination = owner.parent / ("run-" + uuid.uuid4().hex)
            report = recover(owner, destination)
            print(
                json.dumps(
                    {"recovered_run": str(destination), "status": report["status"], "complete": report["complete"]}
                )
            )
            return report["exit_code"]
        manifest = verify_publication(owner)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print("CI report admission failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
