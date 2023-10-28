"""
Helper script to install focus-time (or upgrade an existing installation).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, urlretrieve, urlcleanup
from zipfile import ZipFile, ZipInfo

DEFAULT_INSTALLATION_DIR = Path.home() / "focus-time-app"
CONFIG_FILE_PATH = Path.home() / "Library" / "Application Support" / "FocusTimeApp" / ".installation_path"


class ZipFileWithPermissions(ZipFile):
    """
    Custom ZipFile class that handles file permissions (e.g. +x which we need).
    See https://stackoverflow.com/a/54748564 why we need this.
    """

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath


def download_latest_version_to_temp() -> Tuple[str, Path]:
    """ Returns the version and the local file path to which the latest release was downloaded. """
    with urlopen("https://api.github.com/repos/focus-time/focus-time-app/releases/latest") as response:
        response_content = response.read()
        json_response = json.loads(response_content)
        release_version: str = json_response["name"]
        download_url = ""
        for asset in json_response["assets"]:
            if "macos" in asset["browser_download_url"]:
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            print("Unable to find the macOS download URL for the latest release, existing")
            sys.exit(1)

    download_location, headers = urlretrieve(download_url)

    return release_version, Path(download_location)


def existing_installation_path() -> Optional[Tuple[str, Path]]:
    if CONFIG_FILE_PATH.is_file():
        try:
            installation_path = Path(CONFIG_FILE_PATH.read_text())
            if installation_path.is_dir():
                version_info_file = installation_path / "focustime-version-info.txt"
                if version_info_file.is_file():
                    existing_version_str = version_info_file.read_text().strip()
                    return existing_version_str, installation_path
        except Exception as e:
            print(f"Warning: error occurred while trying to determine existing installations: {e}")


def set_existing_installation_path(installation_path: Path):
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE_PATH.write_text(str(installation_path))


def install_or_upgrade_app(temp_archive_path: Path, installation_path: Path, is_version_upgrade: bool = False):
    focus_time_binary_path = installation_path / "focus-time"
    is_replace = False
    if installation_path.is_dir():
        # First unregister the background job, to avoid that it fails during the replace operation, and because we
        # want to avoid that the password prompt (triggered by the background job) is shown too early
        subprocess.call([str(focus_time_binary_path), "uninstall"])

        # clean the existing contents
        for f in installation_path.iterdir():
            try:
                shutil.rmtree(f)
            except OSError:
                os.remove(f)

        is_replace = True

    with ZipFileWithPermissions(temp_archive_path, 'r') as zip_file:
        zip_file.extractall(path=installation_path)

    set_existing_installation_path(installation_path)
    urlcleanup()

    if is_replace:
        print("Successfully replaced your focus-time installation.")
        if is_version_upgrade:
            input("Note: the calendar credentials are stored in a macOS Keychain. Keychain detects that the "
                  "'focus-time' binary has changed (due to the version upgrade), and therefore rejects the new "
                  "binary's request to read the credentials, for security reasons. "
                  "Please press <enter> to run the 'sync' command, which shortly "
                  "causes a macOS dialog to show up, asking you to grant 'focus-time' access to the keychain again. "
                  "You have to provide your password and then click 'Always allow'.")

            output = subprocess.check_output([str(focus_time_binary_path), "sync"], shell=True).decode("utf-8")
            print(f"Result of 'sync' command: {output}")
        # Install the background job again
        subprocess.call([str(focus_time_binary_path), "doctor"])
    else:
        print("Successfully installed focus-time")


if __name__ == '__main__':
    print(f"Checking for the latest version and downloading it to a temporary folder ...")
    latest_version, temp_archive_path = download_latest_version_to_temp()
    print(f"Latest version: {latest_version}")

    existing_installation = existing_installation_path()

    if existing_installation:
        existing_version, existing_path = existing_installation
        if input(f"Found an existing version ({existing_version}) in '{existing_path}'. "
                 f"Do you want to overwrite it with a clean installation? If so, type 'y' or 'yes':\n") in ["y", "yes"]:
            install_or_upgrade_app(temp_archive_path, existing_path,
                                   is_version_upgrade=latest_version != existing_version)
            sys.exit(0)

    installation_path = None
    while installation_path is None:
        installation_path_str = input(f"Please provide the absolute path where focus-time should be installed "
                                      f"(leave empty to use default directory '{DEFAULT_INSTALLATION_DIR}')\n")

        if not installation_path_str:
            installation_path_str = str(DEFAULT_INSTALLATION_DIR)

        installation_path = Path(installation_path_str)
        if installation_path.exists():
            print(f"Provided path '{installation_path.absolute()}' already exists, please choose a different location!")
            installation_path = None

    install_or_upgrade_app(temp_archive_path, installation_path)
