import sys
from typing import Optional

from focus_time_app.command_execution.abstract_command_executor import AbstractCommandExecutor

CommandExecutorImpl: Optional[AbstractCommandExecutor] = None

if sys.platform == "win32":
    from focus_time_app.command_execution.impl.win_command_executor import WindowsCommandExecutor

    CommandExecutorImpl = WindowsCommandExecutor()
elif sys.platform == "darwin":
    from focus_time_app.command_execution.impl.macos_command_executor import MacOsCommandExecutor

    CommandExecutorImpl = MacOsCommandExecutor()
else:
    raise NotImplementedError
