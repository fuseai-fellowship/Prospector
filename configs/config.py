from dynaconf import Dynaconf
import logging
from pathlib import Path

# Get the directory where config.py is located
_BASE_PATH = Path(__file__).parent.parent
_CONFIG_PATH = _BASE_PATH / "configs"

# Load settings with absolute path
settings = Dynaconf(
    settings_files=[str(_CONFIG_PATH / "settings.toml")],
    envvar_prefix="DYNACONF",
    load_dotenv=True,
    environments=True,  # Enable environment support
)

# Safely get logging settings with defaults
logging_settings = settings.get("logging", {})
log_level = getattr(logging, logging_settings.get("log_level", "INFO").upper())
log_format = logging_settings.get(
    "log_format", "%(asctime)s | %(levelname)s | %(message)s"
)

# Setup logging
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger(settings.get("app_name", "ProspectorApp"))
