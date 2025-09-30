from dynaconf import Dynaconf
import logging

# Load settings
settings = Dynaconf(
    settings_files=["configs/settings.toml"],
    envvar_prefix="DYNACONF",
    load_dotenv=True,
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
