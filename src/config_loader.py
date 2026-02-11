import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file immediately
load_dotenv()

CONFIG_DIR = Path.home() / ".config" / "mrp_mongoose"
CONFIG_FILE = CONFIG_DIR / "SHOPIFY_KEYS.yaml"

def load_config():
    """
    Loads configuration, prioritizing environment variables over the config file.
    Returns a dictionary with configuration keys.
    """
    # 1. Defaults / Empty
    config = {
        "SHOPIFY_SHOP_URL": "",
        "SHOPIFY_API_VERSION": "",
        "SHOPIFY_API_KEY": "",
        "SHOPIFY_ACCESS_TOKEN": "",
        "QUERY_INTERVAL": "3"
    }

    # 2. Load from file if exists
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    # Update config with file values, filtering for expected keys
                    for key in config.keys():
                        if key in file_config:
                            config[key] = str(file_config[key])
        except Exception as e:
            print(f"Error loading config file: {e}")

    # 3. Override with Environment Variables (if set and not empty)
    for key in config.keys():
        env_val = os.getenv(key)
        if env_val:
            config[key] = env_val

    return config

def save_config(new_config):
    """
    Saves the provided configuration to the YAML file.
    """
    # Ensure directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Load existing to preserve other keys if any (optional, but good practice)
        final_config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                final_config = yaml.safe_load(f) or {}
        
        # Update with new values
        for key, value in new_config.items():
            final_config[key] = value
            
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(final_config, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False

def get_config_value(key, default=None):
    """
    Helper to get a single config value.
    This effectively reloads config each time, which is fine for this scale,
    ensuring we get the latest if file changed.
    """
    config = load_config()
    return config.get(key, default)
