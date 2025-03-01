import yaml
import importlib.resources

config_path = importlib.resources.files(__package__) / "config.yaml"

with config_path.open() as f:
    config = yaml.safe_load(f)

SERVER_ADDR = config["network"]["server_addr"]
SERVER_PORT = config["network"]["server_port"]
DEBUG = config["debug"]

__all__ = [
    "SERVER_ADDR",
    "SERVER_PORT",
    "DEBUG",
]
