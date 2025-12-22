
import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.getcwd())

try:
    from games.0_0_biohazard.game_config import GameConfig
    from src.config.config import Config
    
    print("Config file:", sys.modules['src.config.config'].__file__)
    print("Config.construct_paths:", Config.construct_paths)
    
    c = GameConfig()
    print("GameConfig initialized successfully")
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
