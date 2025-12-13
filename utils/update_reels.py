import csv
import random
import os

def update_reel_file(filepath, num_s, num_g):
    with open(filepath, 'r') as f:
        lines = [line.strip().split(',') for line in f.readlines() if line.strip()]

    rows = len(lines)
    cols = len(lines[0])
    
    # Flatten for easier random selection, but keep track of indices
    candidates = []
    for r in range(rows):
        for c in range(cols):
            if lines[r][c].startswith('L'): # Only replace Low symbols
                candidates.append((r, c))

    # Shuffle candidates to pick random spots
    random.shuffle(candidates)

    # Inject S
    for _ in range(num_s):
        if not candidates: break
        r, c = candidates.pop()
        lines[r][c] = 'S'

    # Inject G
    for _ in range(num_g):
        if not candidates: break
        r, c = candidates.pop()
        lines[r][c] = 'G'

    # Write back
    with open(filepath, 'w') as f:
        for line in lines:
            f.write(','.join(line) + '\n')
    
    print(f"Updated {filepath}: Added {num_s} Scatters and {num_g} Guillotines.")

base_path = "/workspaces/math-sdk/games/0_0_guillotine/reels"

# BR0: Base Game - Needs significant boost
update_reel_file(os.path.join(base_path, "BR0.csv"), num_s=15, num_g=15)

# FR0: FS3 - Needs boost
update_reel_file(os.path.join(base_path, "FR0.csv"), num_s=8, num_g=12)

# FR4: FS4 - Needs boost
update_reel_file(os.path.join(base_path, "FR4.csv"), num_s=8, num_g=12)

# FR5: FS5 - Needs boost
update_reel_file(os.path.join(base_path, "FR5.csv"), num_s=8, num_g=12)
