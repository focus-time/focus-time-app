import random
import string
import subprocess
import sys
from pathlib import Path
from typing import Optional

CI_ENV_NAMESPACE_OVERRIDE = "ci-runner"


def get_random_event_name_postfix() -> str:
    source = string.ascii_letters + string.digits
    return ''.join((random.choice(source) for i in range(8)))


def get_frozen_binary_path() -> str:
    binary_ext = ".exe" if sys.platform == "win32" else ""
    return str(Path(__file__).parent.parent.parent / "dist" / "focus-time" / f"focus-time{binary_ext}")


def run_cli_command_handle_output_error(cli_command: str, additional_args: Optional[list[str]] = None):
    try:
        command_and_args = [get_frozen_binary_path(), cli_command]
        if additional_args:
            command_and_args.extend(additional_args)
        finished_process = subprocess.run(command_and_args, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Handle the error explicitly, because the stringification of CalledProcessError does not include stdout
        # or stderr, which is very useful for diagnosing errors
        raise RuntimeError(
            f"Encountered CalledProcessError: {e}.\nStdout:\n{e.stdout.decode('utf-8')}"
            f"\n\nStderr:\n{e.stderr.decode('utf-8')}") from None
    return finished_process.stdout.decode("utf-8")
