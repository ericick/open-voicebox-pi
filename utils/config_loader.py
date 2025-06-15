import yaml
from pathlib import Path

def load_config(config_path: str = 'config/config.yaml'):
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config
