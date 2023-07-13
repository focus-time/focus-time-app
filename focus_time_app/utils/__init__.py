import sys
from os import getenv

CI_ENV_VAR_NAME = "CI"  # keep the value in sync with env vars set in the CI/CD YAML (workflow) files


def is_production_environment() -> bool:
    return getattr(sys, 'frozen', False)


def get_environment_suffix() -> str:
    """
    Returns either an empty string for production environments, or "-ci" or "-dev".

    Background: by "environment" we mean storage locations (e.g. on disk for the logs, or in an OS-native credentials
    manager used under-the-hood by AbstractCalendarAdapter implementations). To avoid that automated (CI) tests
    interfere with the developer setup or a productive installation, we differentiate not only between dev and prod,
    but also between dev and CI.
    """
    if getenv(CI_ENV_VAR_NAME, None) is not None:
        return "-ci"
    if is_production_environment():
        return ""
    return "-dev"
