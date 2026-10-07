"""Preserve explicit CI module ownership after PowerShell child startup."""

import base64
import json
from pathlib import Path


def isolated_command(command, environment):
    if not environment.get("LOTM_CI_MODULE_ROOT"):
        return command
    if "-File" in command:
        arguments = command[command.index("-File") + 1 :]
    elif "-Command" in command:
        position = command.index("-Command")
        if len(command) != position + 2:
            raise ValueError("Owned inline command requires one complete expression")
        arguments = ["-Command", command[position + 1]]
    else:
        return command
    wrapper = Path(__file__).with_name("Invoke-OwnedPowerShell.ps1")
    payload = base64.b64encode(json.dumps(arguments).encode("utf-8")).decode("ascii")
    return [command[0], "-NoProfile", "-File", str(wrapper), "-Payload", payload]
