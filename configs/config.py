from dynaconf import Dynaconf

# Load settings
settings = Dynaconf(
    settings_files=["configs/settings.toml", "configs/.secrets.toml"],
    envvar_prefix="DYNACONF",
    load_dotenv=True,
)
