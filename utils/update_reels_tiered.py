import csv
import random
import os

def reset_and_update_reel(filepath, num_s, num_g, high_boost=0):
    with open(filepath, 'r') as f:
        lines = [line.strip().split(',') for line in f.readlines() if line.strip()]

    rows = len(lines)
    cols = len(lines[0])
    
    # 1. Reset existing S and G to L5 (safe low symbol)
    for r in range(rows):
        for c in range(cols):
            if lines[r][c] in ['S', 'G']:
                lines[r][c] = 'L5'

    # 2. Identify candidates for replacement (Low symbols)
    candidates = []
    for r in range(rows):
        for c in range(cols):
            if lines[r][c].startswith('L'):
                candidates.append((r, c))

    random.shuffle(candidates)

    # 3. Inject S (Scatters)
    for _ in range(num_s):
        if not candidates: break
        r, c = candidates.pop()
        lines[r][c] = 'S'

    # 4. Inject G (Guillotines)
    for _ in range(num_g):
        if not candidates: break
        r, c = candidates.pop()
        lines[r][c] = 'G'
        
    # 5. Boost High Symbols (Replace L with H1)
    for _ in range(high_boost):
        if not candidates: break
        r, c = candidates.pop()
        lines[r][c] = 'H1'

    # Write back
    with open(filepath, 'w') as f:
        for line in lines:
            f.write(','.join(line) + '\n')
    
    print(f"Updated {filepath}: {num_s} S, {num_g} G, {high_boost} H1 boost.")

base_path = "/workspaces/math-sdk/games/0_0_guillotine/reels"

# BR0: Base Game - Moderate
# Increased to boost RTP
reset_and_update_reel(os.path.join(base_path, "BR0.csv"), num_s=12, num_g=12, high_boost=5)

# FR0: FS3 - Better than Base
reset_and_update_reel(os.path.join(base_path, "FR0.csv"), num_s=10, num_g=20, high_boost=20)

# FR4: FS4 - Better than FS3
reset_and_update_reel(os.path.join(base_path, "FR4.csv"), num_s=10, num_g=30, high_boost=40)

# FR5: FS5 - Best
reset_and_update_reel(os.path.join(base_path, "FR5.csv"), num_s=10, num_g=40, high_boost=60)
