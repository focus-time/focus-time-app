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
        if LooseVersion(platform.mac_ver()[0]) < LooseVersion("12"):
            raise ValueError(f"The Focus Time App does not support your macOS version '{platform.mac_ver()[0]}' which "
                             f"is too old")
    else:
        raise ValueError(f"The Focus Time App does not support  your platform {sys.platform}")
