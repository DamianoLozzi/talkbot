import os
import configparser
from typing import Optional, Any

class Config:
    _instance: Optional['Config'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, 'initialized', False):
            return

        # Percorso del file locale facoltativo (IGNORATO in Git)
        self.config_path: str = os.path.join(os.path.dirname(__file__), "../config.ini")

        # Carica eventualmente config.ini se presente
        parser = configparser.RawConfigParser()
        if os.path.isfile(self.config_path):
            parser.read(self.config_path)

        # Helper: leggi da ENV, altrimenti fallback su config.ini, altrimenti errore
        def get_env_or_cfg(section: str, option: str, env_var: str, default: Optional[Any] = None, required: bool = False, cast=None):
            # 1) se c’è ENV, usala
            val = os.getenv(env_var)
            if val is not None:
                return cast(val) if (cast and val is not None) else val

            # 2) altrimenti, se nel file config.ini c’è, prendila
            try:
                if parser.has_option(section, option):
                    raw = parser.get(section, option)
                    return cast(raw) if (cast and raw is not None) else raw
            except Exception:
                pass

            # 3) fallback su default
            if default is not None:
                return default

            # 4) se è obbligatoria => errore
            if required:
                raise RuntimeError(f"Missing required config for [{section}]{option}. Set environment variable '{env_var}'.")
            return None

        # NEXTCLOUD
        self.NEXTCLOUD_URL = get_env_or_cfg("NEXTCLOUD", "url", "NEXTCLOUD_URL", required=True)
        self.NEXTCLOUD_USERNAME = get_env_or_cfg("NEXTCLOUD", "username", "NEXTCLOUD_USERNAME", required=True)
        self.NEXTCLOUD_PASSWORD = get_env_or_cfg("NEXTCLOUD", "password", "NEXTCLOUD_PASSWORD", required=True)
        self.NEXTCLOUD_MAX_RETRIES = int(get_env_or_cfg("NEXTCLOUD", "max_retries", "NEXTCLOUD_MAX_RETRIES", default="5"))
        self.NEXTCLOUD_RETRY_DELAY = float(get_env_or_cfg("NEXTCLOUD", "retry_delay", "NEXTCLOUD_RETRY_DELAY", default="2"))
        self.NEXTCLOUD_CHECK_INTERVAL = int(get_env_or_cfg("NEXTCLOUD", "check_interval", "NEXTCLOUD_CHECK_INTERVAL", default="5"))
        self.NEXTCLOUD_BACKOFF = float(get_env_or_cfg("NEXTCLOUD", "backoff", "NEXTCLOUD_BACKOFF", default="1.2"))

        # OLLAMA
        self.OLLAMA_HOST = get_env_or_cfg("OLLAMA", "host", "OLLAMA_HOST", required=True)
        self.OLLAMA_MODEL = get_env_or_cfg("OLLAMA", "model", "OLLAMA_MODEL", required=True)
        self.OLLAMA_SYSTEM_PROMPT = get_env_or_cfg("OLLAMA", "system_prompt", "OLLAMA_SYSTEM_PROMPT", required=True)
        self.OLLAMA_ACTOR_ID = get_env_or_cfg("OLLAMA", "actor_id", "OLLAMA_ACTOR_ID", required=True)

        # LOGGING
        self.LOG_DIRECTORY = get_env_or_cfg("LOGGING", "LOG_DIRECTORY", "LOG_DIRECTORY", default="./logs")
        self.LOG_FILENAME = get_env_or_cfg("LOGGING", "LOG_FILENAME", "LOG_FILENAME", default="archie.log")
        self.JSON_LOG_FILENAME = get_env_or_cfg("LOGGING", "JSON_LOG_FILENAME", "JSON_LOG_FILENAME", default="archie.json")
        self.CONSOLE_COLORIZE = int(get_env_or_cfg("LOGGING", "CONSOLE_COLORIZE", "CONSOLE_COLORIZE", default="1"))
        self.LOG_COLORIZE = int(get_env_or_cfg("LOGGING", "LOG_COLORIZE", "LOG_COLORIZE", default="0"))
        self.JSON_COLORIZE = int(get_env_or_cfg("LOGGING", "JSON_COLORIZE", "JSON_COLORIZE", default="0"))
        self.LOG_LEVEL = get_env_or_cfg("LOGGING", "LOG_LEVEL", "LOG_LEVEL", default="INFO")
        self.LOG_FORMAT = get_env_or_cfg("LOGGING", "LOG_FORMAT", "LOG_FORMAT", default="%(asctime)s | %(levelname)s | %(message)s")
        self.DATE_FORMAT = get_env_or_cfg("LOGGING", "DATE_FORMAT", "DATE_FORMAT", default="%Y-%m-%d %H:%M:%S")

        self.initialized = True

