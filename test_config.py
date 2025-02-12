import yaml
from api import FullConfig
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

def test_config():
    try:
        print(f"Loading config from {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as f:
            config_dict = yaml.safe_load(f)
            print("Config loaded from YAML successfully")
            print("\nValidating against Pydantic model...")
            config = FullConfig(**config_dict)
            print("Config validated successfully!")
            print("\nConfig contents:")
            print(config.dict())
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_config()
