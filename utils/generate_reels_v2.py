import csv
import random
import os

# Configuration
REEL_LENGTH = 160
OUTPUT_DIR = "/workspaces/math-sdk/games/0_0_guillotine/reels"

def create_base_reel(reel_idx):
    # BR0: Base Game
    # S: 11 (Targeting ~1/203 trigger)
    # G: R0, R1 = 0. R2, R3, R4 = 4 (Low frequency)
    # Highs: Spread out
    
    strip = []
    
    # Counts
    counts = {
        'S': 11,
        'H1': 10, 'H2': 10, 'H3': 10, 'H4': 10, 'H5': 10,
        'L1': 18, 'L2': 18, 'L3': 18, 'L4': 18, 'L5': 18
    }
    
    # Adjust for G
    if reel_idx in [0, 1]:
        counts['G'] = 0
        counts['L1'] += 4 # Fill gap
    else:
        counts['G'] = 4
    
    # Build list
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    # Fill to exact length if needed (should be 157-161)
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    
    # Enforce G placement (Bottom of strip - symbolic)
    # And ensure no stacks of Highs
    # We'll do a simple pass to break up High stacks
    for i in range(len(strip) - 1):
        if strip[i].startswith('H') and strip[i+1].startswith('H'):
            # Swap i+1 with a random Low
            low_indices = [k for k, s in enumerate(strip) if s.startswith('L')]
            if low_indices:
                swap_idx = random.choice(low_indices)
                strip[i+1], strip[swap_idx] = strip[swap_idx], strip[i+1]

    return strip

def create_fr0_reel(reel_idx):
    # FR0 (FS3): Main Bonus
    # G: R1, R2, R3 (Indices 1,2,3) -> Focus. R0, R4 -> None/Low
    # Clumps of H1, H2, H3
    
    strip = []
    counts = {
        'S': 11,
        'H1': 15, 'H2': 15, 'H3': 15, 'H4': 8, 'H5': 8,
        'L1': 15, 'L2': 15, 'L3': 15, 'L4': 15, 'L5': 15
    }
    
    if reel_idx in [1, 2, 3]:
        counts['G'] = 12 # Moderate/High
    else:
        counts['G'] = 0
        counts['L1'] += 12
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    
    # Create Clumps for H1, H2, H3
    # Sort of hard to force clumps in a shuffled list without logic
    # We'll just accept the random distribution which naturally clumps sometimes
    # or we could sort sections. Let's leave random for now.
    return strip

def create_fr4_reel(reel_idx):
    # FR4 (FS4): High Volatility
    # G: R0, R1, R2 -> Focus.
    # High density H4, H5
    
    strip = []
    counts = {
        'S': 11,
        'H1': 5, 'H2': 5, 'H3': 5, 'H4': 25, 'H5': 25,
        'L1': 12, 'L2': 12, 'L3': 12, 'L4': 12, 'L5': 12
    }
    
    if reel_idx in [0, 1, 2]:
        counts['G'] = 18 # High
    else:
        counts['G'] = 2 # Low
        counts['L1'] += 16
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    return strip

def create_fr5_reel(reel_idx):
    # FR5 (FS5): Jackpot
    # G: R1, R2, R3 -> Saturated.
    # Saturate H5. Remove Lows.
    
    strip = []
    counts = {
        'S': 11,
        'H1': 2, 'H2': 2, 'H3': 2, 'H4': 2, 'H5': 60,
        'L1': 5, 'L2': 5, 'L3': 5, 'L4': 5, 'L5': 5
    }
    
    if reel_idx in [1, 2, 3]:
        counts['G'] = 40 # Very High
    else:
        counts['G'] = 5
        counts['H5'] += 35
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('H5') # Fill with H5
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    return strip

def write_reel_file(filename, creator_func):
    reels = [creator_func(i) for i in range(5)]
    # Transpose to rows
    rows = []
    for i in range(REEL_LENGTH):
        row = [reels[j][i] for j in range(5)]
        rows.append(row)
        
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Generated {filepath}")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    write_reel_file("BR0.csv", create_base_reel)
    write_reel_file("FR0.csv", create_fr0_reel)
    write_reel_file("FR4.csv", create_fr4_reel)
    write_reel_file("FR5.csv", create_fr5_reel)
