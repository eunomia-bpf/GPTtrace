import os

from getpass import getpass
from pathlib import Path
from typing import Any
from click import UsageError

CONFIG_FOLDER = os.path.expanduser("~/.config")
GPT_TRACE_CONFIG_FOLDER = Path(CONFIG_FOLDER) / "gpt_trace"
GPT_TRACE_CONFIG_PATH = GPT_TRACE_CONFIG_FOLDER / ".gpt_trace_rc"

OPENAI_API_KEY = "OPENAI_API_KEY"

PROJECT_ROOT_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC_PATH = PROJECT_ROOT_PATH / "bpf_tutorial"/ "src"
DATA_SAVE_PATH = PROJECT_ROOT_PATH / "data_save"
VECTOR_DATABASE_PATH = DATA_SAVE_PATH / "vector_database"
BCC_FUNC_CALL_PATH = DATA_SAVE_PATH / "funcs.json"
MODEL_NAME = "gpt-3.5-turbo-0613"

DEFAULT_CONFIG = {
    "DEFAULT_MODEL": os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "OPENAI_API_KEY"),
    "DATA_SAVE_PATH": os.getenv("DATA_SAVE_PATH", DATA_SAVE_PATH),
    "VECTOR_DATABASE_PATH": os.getenv("VECTOR_DATABASE_PATH", VECTOR_DATABASE_PATH),
    "BCC_FUNC_CALL_PATH": os.getenv("BCC_FUNC_CALL_PATH", BCC_FUNC_CALL_PATH),
    "DOC_PATH": os.getenv("DOC_PATH", DOC_PATH),
    "MODEL_NAME": os.getenv("MODEL_NAME", MODEL_NAME)
}

class Config(dict):
    """
    A dictionary for handling configuration items in this project.
    """
    def __init__(self, config_path: Path, **defaults: Any):
        """
        Initializes a Config object.

        :param config_path: The path to the configuration file.
        :param **defaults: Default values for configuration options.
        """
        self.config_path = config_path

        if self._exists:
            self._read()
            has_new_config = False
            for key, value in defaults.items():
                if key not in self:
                    has_new_config = True
                    self[key] = value
            if has_new_config:
                self._write()
        else:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Don't write API key to config file if it is in the environment.
            if not defaults.get("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
                __api_key = getpass(prompt="Please enter your OpenAI API key: ")
                defaults["OPENAI_API_KEY"] = __api_key
            super().__init__(**defaults)
            self._write()


    @property
    def _exists(self) -> bool:
        """
        Checks if the configuration file exists.

        :return: True if the configuration file exists, False otherwise.
        """
        return self.config_path.exists()

    def _write(self) -> None:
        """
        Writes the configuration options to the configuration file.
        """
        with open(self.config_path, "w", encoding="utf-8") as file:
            string_config = ""
            for key, value in self.items():
                string_config += f"{key}={value}\n"
            file.write(string_config)

    def _read(self) -> None:
        """
        Reads the configuration options from the configuration file.
        """
        with open(self.config_path, "r", encoding="utf-8") as file:
            for line in file:
                if not line.startswith("#"):
                    key, value = line.strip().split("=")
                    self[key] = value

    def get(self, key: str) -> str:  # type: ignore
        """
        Retrieves the value associated with the specified key.

        :param key: The key of the configuration option to retrieve.
        :return: The value associated with the specified key.
        """
        # Prioritize environment variables over config file.
        value = os.getenv(key) or super().get(key)
        if not value:
            raise UsageError(f"Missing config key: {key}")
        return value

cfg = Config(GPT_TRACE_CONFIG_PATH, **DEFAULT_CONFIG)
