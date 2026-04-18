import unittest
import os
import shutil
from pathlib import Path
import sys
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config_loader import load_config, save_config, CONFIG_FILE

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        # Backup existing config if any
        self.backup_config = None
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                self.backup_config = f.read()
            CONFIG_FILE.unlink()
            
        # Clear specific env vars
        self.env_vars = ["SHOPIFY_SHOP_URL", "SHOPIFY_API_VERSION", "SHOPIFY_API_KEY", "SHOPIFY_ACCESS_TOKEN", "QUERY_INTERVAL"]
        self.old_env = {}
        for key in self.env_vars:
            self.old_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        # Restore env vars
        for key, val in self.old_env.items():
            if val is not None:
                os.environ[key] = val
            elif key in os.environ:
                del os.environ[key]
        
        # Restore config file
        if self.backup_config:
            # Ensure dir exists
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                f.write(self.backup_config)
        elif CONFIG_FILE.exists():
            CONFIG_FILE.unlink()

    def test_load_defaults(self):
        config = load_config()
        self.assertEqual(config["QUERY_INTERVAL"], "3")
        self.assertEqual(config["SHOPIFY_SHOP_URL"], "")

    def test_save_and_load_file(self):
        new_config = {
            "SHOPIFY_SHOP_URL": "test-shop.myshopify.com",
            "QUERY_INTERVAL": "10"
        }
        save_config(new_config)
        
        loaded = load_config()
        self.assertEqual(loaded["SHOPIFY_SHOP_URL"], "test-shop.myshopify.com")
        self.assertEqual(loaded["QUERY_INTERVAL"], "10")

    def test_env_priority(self):
        # Set file config
        save_config({"SHOPIFY_SHOP_URL": "file-shop.com"})
        
        # Set env var
        os.environ["SHOPIFY_SHOP_URL"] = "env-shop.com"
        
        loaded = load_config()
        self.assertEqual(loaded["SHOPIFY_SHOP_URL"], "env-shop.com")

if __name__ == '__main__':
    unittest.main()
