import logging
import os.path
import sys
from logging.handlers import RotatingFileHandler

import typer

project_root_path = os.path.dirname(os.path.dirname(__file__))
if project_root_path not in sys.path:
    sys.path.append(project_root_path)
from tendo.singleton import SingleInstance, SingleInstanceException
from focus_time_app.cli.cli import app
from focus_time_app.configuration.persistence import Persistence
from focus_time_app.utils.compatibility_checker import check_os_compatibility


def configure_logging():
    log_file_path = Persistence.get_storage_directory() / "log.txt"
    logging.basicConfig(
        handlers=[RotatingFileHandler(log_file_path, maxBytes=1024 * 1024 * 5, backupCount=2, encoding="utf-8")],
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S")

    # Silence the debug messages emitted by "SingleInstance()" when successfully acquiring a lock
    # (it would spam the log every minute)
    logging.getLogger("tendo.singleton").setLevel(logging.WARNING)
    # Silence the logger because at DEBUG it emits messages that contain credentials
    logging.getLogger("requests_oauthlib.oauth2_session").setLevel(logging.INFO)
    # Silence chatty Keyring logger
    logging.getLogger("keyring.backend").setLevel(logging.INFO)


def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    if issubclass(exc_type, KeyboardInterrupt):
        return
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


def configure_exception_hook():
    """
    When unexpected exceptions occur, we want OUR(!) handler to handle them, by printing them and logging them to file.

    Unfortunately, Typer's "main.py" module is already loaded PRIOR to the execution of configure_exception_hook(), and
    there Typer already internally stores a reference to Python's default sys.excepthook, and thus OUR hook is never
    called. Consequently, we need to overwrite typer's internally-stored reference here again, to point to OUR hook.
    """
    sys.excepthook = handle_unhandled_exception

    if not getattr(typer.main, "_original_except_hook"):
        raise RuntimeError("Typer's internal implementation regarding the exception hook has changed")
    setattr(typer.main, "_original_except_hook", handle_unhandled_exception)


if __name__ == '__main__':
    configure_logging()
    configure_exception_hook()
    try:
        SingleInstance()
    except SingleInstanceException:
        print("Another instance of the Focus time app is already running")
        exit(1)

    try:
        check_os_compatibility()
    except ValueError as e:
        print(str(e))
        exit(1)

    app()
