import os
from pathlib import Path
from typing import Any, Dict, Optional

import toml
from pydantic import BaseModel, BaseSettings, validator

from comicer.source import Source

AM_I_IN_A_DOCKER_CONTAINER = os.environ.get(
    "AM_I_IN_A_DOCKER_CONTAINER", False
)

if AM_I_IN_A_DOCKER_CONTAINER:
    USER_CONFIG_PATH = Path("/config")
else:
    USER_CONFIG_PATH = Path("~/.comicer").expanduser()

PROJECT_DIR = Path(__file__).parent.parent.absolute()


def default_toml_config_settings_source(
    settings: BaseSettings,
) -> Dict[str, Any]:
    default_config_path = Path(os.path.join(PROJECT_DIR, "config.toml"))
    if not default_config_path.exists():
        return {}
    return toml.load(default_config_path)


def user_toml_config_settings_source(
    settings: BaseSettings,
) -> Dict[str, Any]:
    user_config_file_path = USER_CONFIG_PATH.joinpath("config.toml")
    if not user_config_file_path.exists():
        return {}
    return toml.load(user_config_file_path)


class ExpanduserPathMixin(BaseModel):
    @validator("*")
    def expanduser_path(cls, value):
        if isinstance(value, Path):
            value = value.expanduser()
            if not value.is_absolute():
                raise ValueError("path must absolute")
            return value
        return value


class SpiderConfig(ExpanduserPathMixin, BaseModel):
    save_path: Optional[Path]
    source: Source


class GlobalConfig(ExpanduserPathMixin, BaseSettings):
    save_path: Path = Path("/comic")
    state_path: Path = USER_CONFIG_PATH.joinpath("state")
    log_level: Optional[int | str] = "INFO"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    https_proxy: Optional[str] = None
    http_proxy: Optional[str] = None
    mox: Optional[SpiderConfig] = None

    class Config:
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                user_toml_config_settings_source,
                default_toml_config_settings_source,
                file_secret_settings,
            )


CONFIG = GlobalConfig()
if __name__ == "__main__":
    print(CONFIG)
