"""Native pytest phase evidence; loaded explicitly, never a global plugin."""

import json
import os
from pathlib import Path

REPORTS = []
COLLECTION_ERRORS = []
INTERRUPTED = False


def pytest_runtest_logreport(report):
    REPORTS.append(
        {
            "id": report.nodeid,
            "phase": report.when,
            "outcome": report.outcome,
            "xfail": bool(getattr(report, "wasxfail", False)),
            "duration": report.duration,
        }
    )


def pytest_collectreport(report):
    if report.failed:
        COLLECTION_ERRORS.append({"id": report.nodeid, "diagnostic": str(report.longrepr)})


def pytest_keyboard_interrupt(excinfo):
    global INTERRUPTED
    # pytest also calls this hook for its collection-abort Interrupted exception (exit 2).
    INTERRUPTED = excinfo.type is KeyboardInterrupt


def pytest_sessionfinish(session, exitstatus):
    path = Path(os.environ["NATIVE_PHASE_REPORT"])
    path.write_text(
        json.dumps(
            {
                "framework": "pytest",
                "collected": session.testscollected,
                "exit_code": int(exitstatus),
                "reports": REPORTS,
                "collection_errors": COLLECTION_ERRORS,
                "interrupted": INTERRUPTED,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
