import os
import configparser
from typing import Optional, Any, TypeVar, Callable

_T = TypeVar("_T")

class Config:
    _instance: Optional['Config'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, 'initialized', False):
            return

        self.config_path = os.path.join(
            os.fspath(os.path.dirname(__file__)), 
            os.fspath("../config.ini")
        )
        parser = configparser.RawConfigParser()
        if os.path.isfile(self.config_path):
            parser.read(self.config_path)

        def get_env_or_cfg(
            section: str,
            option: str,
            env_var: str,
            default: Optional[_T] = None,
            required: bool = False,
            cast: Optional[Callable[[str], _T]] = None
        ) -> _T:
            val = os.getenv(env_var)
            if val is not None:
                return cast(val) if cast else val  # type: ignore

            if parser.has_option(section, option):
                raw = parser.get(section, option)
                return cast(raw) if cast else raw  # type: ignore

            if default is not None:
                return default

            if required:
                raise RuntimeError(
                    f"Missing required config for [{section}]{option}. "
                    f"Set environment variable '{env_var}'."
                )
            return None  # type: ignore

        # ----------------------------
        # Nextcloud
        # ----------------------------
        self.NEXTCLOUD_URL: str = get_env_or_cfg(
            "NEXTCLOUD", "url", "NEXTCLOUD_URL", required=True, cast=str
        )
        self.NEXTCLOUD_USERNAME: str = get_env_or_cfg(
            "NEXTCLOUD", "username", "NEXTCLOUD_USERNAME", required=True, cast=str
        )
        self.NEXTCLOUD_PASSWORD: str = get_env_or_cfg(
            "NEXTCLOUD", "password", "NEXTCLOUD_PASSWORD", required=True, cast=str
        )
        self.NEXTCLOUD_MAX_RETRIES: int = get_env_or_cfg(
            "NEXTCLOUD", "max_retries", "NEXTCLOUD_MAX_RETRIES", default=5, cast=int
        )
        self.NEXTCLOUD_RETRY_DELAY: float = get_env_or_cfg(
            "NEXTCLOUD", "retry_delay", "NEXTCLOUD_RETRY_DELAY", default=2.0, cast=float
        )
        self.NEXTCLOUD_CHECK_INTERVAL: int = get_env_or_cfg(
            "NEXTCLOUD", "check_interval", "NEXTCLOUD_CHECK_INTERVAL", default=5, cast=int
        )
        self.NEXTCLOUD_BACKOFF: float = get_env_or_cfg(
            "NEXTCLOUD", "backoff", "NEXTCLOUD_BACKOFF", default=1.2, cast=float
        )

        # ----------------------------
        # Ollama
        # ----------------------------
        self.OLLAMA_HOST: str = get_env_or_cfg(
            "OLLAMA", "host", "OLLAMA_HOST", required=True, cast=str
        )
        self.OLLAMA_MODEL: str = get_env_or_cfg(
            "OLLAMA", "model", "OLLAMA_MODEL", required=True, cast=str
        )
        self.OLLAMA_SYSTEM_PROMPT: str = get_env_or_cfg(
            "OLLAMA", "system_prompt", "OLLAMA_SYSTEM_PROMPT", required=True, cast=str
        )
        self.OLLAMA_ACTOR_ID: str = get_env_or_cfg(
            "OLLAMA", "actor_id", "OLLAMA_ACTOR_ID", required=True, cast=str
        )

        # ----------------------------
        # Logging
        # ----------------------------
        self.LOG_DIRECTORY: str = get_env_or_cfg(
            "LOGGING", "LOG_DIRECTORY", "LOG_DIRECTORY", default="./logs", cast=str
        )
        self.LOG_FILENAME: str = get_env_or_cfg(
            "LOGGING", "LOG_FILENAME", "LOG_FILENAME", default="talkbot.log", cast=str
        )
        self.JSON_LOG_FILENAME: str = get_env_or_cfg(
            "LOGGING", "JSON_LOG_FILENAME", "JSON_LOG_FILENAME", default="talkbot.json", cast=str
        )
        self.CONSOLE_COLORIZE: int = get_env_or_cfg(
            "LOGGING", "CONSOLE_COLORIZE", "CONSOLE_COLORIZE", default=1, cast=int
        )
        self.LOG_COLORIZE: int = get_env_or_cfg(
            "LOGGING", "LOG_COLORIZE", "LOG_COLORIZE", default=0, cast=int
        )
        self.JSON_COLORIZE: int = get_env_or_cfg(
            "LOGGING", "JSON_COLORIZE", "JSON_COLORIZE", default=0, cast=int
        )
        self.LOG_LEVEL: str = get_env_or_cfg(
            "LOGGING", "LOG_LEVEL", "LOG_LEVEL", default="INFO", cast=str
        )
        self.LOG_FORMAT: str = get_env_or_cfg(
            "LOGGING", "LOG_FORMAT", "LOG_FORMAT",
            default="%(asctime)s | %(levelname)s | %(message)s", cast=str
        )
        self.DATE_FORMAT: str = get_env_or_cfg(
            "LOGGING", "DATE_FORMAT", "DATE_FORMAT", default="%Y-%m-%d %H:%M:%S", cast=str
        )

        self.initialized = True