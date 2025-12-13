import random
import time
import os
import sys

# --- CONFIGURATION ---
ROWS = 3
COLS = 5
# Define symbols with ANSI color codes for visual distinction
# \033[91m = Red, 92m = Green, 93m = Yellow, 94m = Blue, 95m = Magenta, 0m = Reset
SYMBOLS = {
    'WILD':  '\033[91mWILD \033[0m',  # Red
    'HIGH':  '\033[93mHIGH \033[0m',  # Yellow
    'MID':   '\033[94mMID  \033[0m',   # Blue
    'LOW':   '\033[92mLOW  \033[0m',   # Green
    'SCAT':  '\033[95mSCAT \033[0m'   # Magenta
}

def clear_console():
    """Clears the terminal screen. Works in Linux/Codespaces."""
    os.system('clear')

def get_random_grid():
    keys = list(SYMBOLS.keys())
    return [[SYMBOLS[random.choice(keys)] for _ in range(COLS)] for _ in range(ROWS)]

def draw_interface(grid, spin_count):
    clear_console()
    
    # UI Header
    print(f"\n   --- CODESPACE VISUAL TEST RUNNER ---")
    print(f"   Spin #{spin_count}")
    print("   " + "=" * 37)

    # Draw Grid
    print("   " + "+-------" * COLS + "+")
    for row in grid:
        row_str = "   |"
        for cell in row:
            # We assume the raw text length is 5 chars + color codes
            # The padding allows the color codes to render without breaking alignment
            row_str += f" {cell} |" 
        print(row_str)
        print("   " + "+-------" * COLS + "+")
    
    print("\n   [CTRL+C to Stop]")

def run():
    spin = 0
    try:
        while True:
            spin += 1
            grid = get_random_grid()
            draw_interface(grid, spin)
            
            # Pause to let the user see the result
            time.sleep(1.5) 
            
    except KeyboardInterrupt:
        print("\n\n   Test Stopped by User.")

if __name__ == "__main__":
    run()