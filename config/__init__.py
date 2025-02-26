import yaml
import importlib.resources

config_path = importlib.resources.files(__package__) / "config.yaml"

with config_path.open() as f:
    config = yaml.safe_load(f)

LOCALHOST = config["network"]["localhost"]
SERVER_PORT = config["network"]["server_port"]
DEBUG = config["debug"]

__all__ = [
    "LOCALHOST",
    "SERVER_PORT",
    "DEBUG",
]
