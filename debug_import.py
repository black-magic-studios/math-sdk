
import sys
import os
print("sys.path:", sys.path)
try:
    import src.config.config
    print("src.config.config file:", src.config.config.__file__)
    from src.config.config import Config
    print("Config.construct_paths signature:", Config.construct_paths)
except ImportError as e:
    print("ImportError:", e)
