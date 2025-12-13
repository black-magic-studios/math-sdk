import csv
import random
import os

# Configuration
REEL_LENGTH = 160
OUTPUT_DIR = "/workspaces/math-sdk/games/0_0_guillotine/reels"

def create_base_reel(reel_idx):
    # BR0: Base Game (Maintained)
    strip = []
    counts = {
        'S': 11,
        'H1': 10, 'H2': 10, 'H3': 10, 'H4': 10, 'H5': 10,
        'L1': 18, 'L2': 18, 'L3': 18, 'L4': 18, 'L5': 18
    }
    
    if reel_idx in [0, 1]:
        counts['G'] = 0
        counts['L1'] += 4
    else:
        counts['G'] = 4
    
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    return strip

def create_fr0_reel(reel_idx):
    # FR0 (FS3): Target 96x
    # Fix: Reel 1 needs heavy stacks of H1-H3 to connect with Wilds on R2-4
    
    strip = []
    
    if reel_idx == 0:
        # Reel 1: Heavy Highs, No G
        counts = {
            'S': 11,
            'G': 0,
            'H1': 30, 'H2': 30, 'H3': 30, 'H4': 5, 'H5': 5,
            'L1': 10, 'L2': 10, 'L3': 10, 'L4': 10, 'L5': 9
        }
    elif reel_idx in [1, 2, 3]:
        # Reels 2, 3, 4: Focus G
        counts = {
            'S': 11,
            'G': 12,
            'H1': 15, 'H2': 15, 'H3': 15, 'H4': 8, 'H5': 8,
            'L1': 15, 'L2': 15, 'L3': 15, 'L4': 15, 'L5': 16
        }
    else:
        # Reel 5: Filler
        counts = {
            'S': 11,
            'G': 0,
            'H1': 15, 'H2': 15, 'H3': 15, 'H4': 15, 'H5': 15,
            'L1': 15, 'L2': 15, 'L3': 15, 'L4': 15, 'L5': 14
        }
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    return strip

def create_fr4_reel(reel_idx):
    # FR4 (FS4): Target 400x
    # Fix: Force G on Reel 1 (High density). High H4/H5 elsewhere.
    
    strip = []
    
    if reel_idx == 0:
        # Reel 1: High G density to ensure it lands
        counts = {
            'S': 11,
            'G': 40, # 25% of strip is G
            'H1': 5, 'H2': 5, 'H3': 5, 'H4': 20, 'H5': 20,
            'L1': 10, 'L2': 10, 'L3': 10, 'L4': 10, 'L5': 14
        }
    else:
        # Reels 2-5: High H4/H5, Moderate G
        counts = {
            'S': 11,
            'G': 15,
            'H1': 5, 'H2': 5, 'H3': 5, 'H4': 30, 'H5': 30,
            'L1': 12, 'L2': 12, 'L3': 12, 'L4': 12, 'L5': 11
        }
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
    strip = strip[:REEL_LENGTH]
    
    random.shuffle(strip)
    return strip

def create_fr5_reel(reel_idx):
    # FR5 (FS5): Target 2000x (Max Potential)
    # Fix: Dilute with Lows to stop hitting 5000x cap every time.
    
    strip = []
    
    # Add ~40% Lows (approx 64 symbols out of 160)
    low_count = 13 # 13 * 5 = 65
    
    if reel_idx in [1, 2, 3]:
        # Center Reels: High G, High H5, but diluted
        counts = {
            'S': 11,
            'G': 30, 
            'H1': 2, 'H2': 2, 'H3': 2, 'H4': 2, 'H5': 45,
            'L1': low_count, 'L2': low_count, 'L3': low_count, 'L4': low_count, 'L5': low_count + 1
        }
    else:
        # Outer Reels
        counts = {
            'S': 11,
            'G': 5,
            'H1': 2, 'H2': 2, 'H3': 2, 'H4': 2, 'H5': 45,
            'L1': low_count, 'L2': low_count, 'L3': low_count, 'L4': low_count, 'L5': low_count + 1
        }
        
    for sym, count in counts.items():
        strip.extend([sym] * count)
        
    while len(strip) < REEL_LENGTH:
        strip.append('L5')
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
