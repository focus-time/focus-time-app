from pathlib import Path

import typer
import yaml

from focus_time_app.configuration.configuration import ConfigurationV1, ConfigurationV1Schema
from focus_time_app.utils import get_environment_suffix

configuration_v1_schema = ConfigurationV1Schema()


class Persistence:
    APP_NAME = "FocusTimeApp"
    MARKER_FILE_NAME = "start_command_was_recently_called"
    CONFIG_FILE_NAME = "configuration.yaml"

    @staticmethod
    def load_configuration() -> ConfigurationV1:
        with Persistence.get_config_file_path().open("rt", encoding="utf-8") as f:
            config_as_dict: dict = yaml.safe_load(f)

        if v := config_as_dict["version"] != 1:
            raise ValueError(f"Detected invalid version {v} of the configuration file. Supported versions are: 1")
        configuration = configuration_v1_schema.load(config_as_dict)
        # Note: once the configuration schema evolves, we can do configuration migrations here
        return configuration

    @staticmethod
    def store_configuration(configuration: ConfigurationV1):
        config_as_dict = configuration_v1_schema.dump(configuration)
        Persistence.get_config_file_path().parent.mkdir(parents=True, exist_ok=True)
        with Persistence.get_config_file_path().open("wt", encoding="utf-8") as f:
            yaml.dump(config_as_dict, f)

    @staticmethod
    def ongoing_focustime_markerfile_exists() -> bool:
        return Persistence._get_marker_file_path().is_file()

    @staticmethod
    def set_ongoing_focustime(ongoing: bool):
        if ongoing:
            Persistence._get_marker_file_path().touch()
        else:
            Persistence._get_marker_file_path().unlink(missing_ok=True)

    @staticmethod
    def get_storage_directory() -> Path:
        app_name = Persistence.APP_NAME + get_environment_suffix()
        return Path(typer.get_app_dir(app_name, roaming=True))

    @staticmethod
    def get_config_file_path() -> Path:
        return Persistence.get_storage_directory() / Persistence.CONFIG_FILE_NAME

    @staticmethod
    def _get_marker_file_path() -> Path:
        return Persistence.get_storage_directory() / Persistence.MARKER_FILE_NAME
