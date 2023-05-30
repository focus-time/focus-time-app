import sys
import platform
from distutils.version import LooseVersion


def check_os_compatibility():
    """
    Determines whether this tool is compatible with the operating system and its specific version. Raises ValueError
    if this is not the case.
    """
    if sys.platform == "win32":
        if LooseVersion(platform.release()) < LooseVersion("10"):
            raise ValueError(f"The Focus Time App does not support your Windows version '{platform.release()}' which "
                             f"is too old")
    elif sys.platform == "darwin":
        pass  # TODO somehow limit to Monterey (12) and newer
    else:
        raise ValueError(f"The Focus Time App does not support  your platform {sys.platform}")
