import sys
from datetime import timedelta
from os import getenv

# keep the values in sync with env vars set in the CI/CD YAML (workflow) files
CI_ENV_VAR_NAME = "CI"


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


def human_readable_timedelta(duration: timedelta) -> str:
    data = {}
    data['days'], remaining = divmod(duration.total_seconds(), 86_400)
    data['hours'], remaining = divmod(remaining, 3_600)
    data['minutes'], data['seconds'] = divmod(remaining, 60)

    del data['seconds']  # we do not need this degree of precision

    time_parts = ((name, round(value)) for name, value in data.items())
    time_parts = [f'{value} {name[:-1] if value == 1 else name}' for name, value in time_parts if value > 0]
    if time_parts:
        return ' '.join(time_parts)
    else:
        return 'below 1 second'
