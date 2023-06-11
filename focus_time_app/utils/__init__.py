import sys
from os import getenv


def is_production_environment(ci_means_dev: bool = True) -> bool:
    # TODO document
    if ci_means_dev:
        return getattr(sys, 'frozen', False) and getenv("CI", None) is None
    return getattr(sys, 'frozen', False)
