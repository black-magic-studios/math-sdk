
import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.getcwd())

try:
    import src
    print("src module:", src)
    print("src file:", src.__file__)
    print("src path:", src.__path__)
    
    import optimization_program
    print("optimization_program file:", optimization_program.__file__)

except ImportError as e:
    print("ImportError:", e)
