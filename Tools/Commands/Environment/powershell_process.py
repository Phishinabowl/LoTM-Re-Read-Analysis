"""Preserve explicit CI module ownership after PowerShell child startup."""

import base64
import json
from pathlib import Path


def isolated_command(command, environment):
    if not environment.get("LOTM_CI_MODULE_ROOT") or "-File" not in command:
        return command
    position = command.index("-File")
    wrapper = Path(__file__).with_name("Invoke-OwnedPowerShell.ps1")
    payload = base64.b64encode(json.dumps(command[position + 1 :]).encode("utf-8")).decode("ascii")
    return [command[0], "-NoProfile", "-File", str(wrapper), "-Payload", payload]
