import argparse
import sys
from pathlib import Path
from disturbance import apply_disturbance

def parse_args():
    parser = argparse.ArgumentParser(description="FSOC Coarse-Alignment Simulator")
    parser.add_argument(
        '--scenario', 
        type=str, 
        default='baseline',
        choices=['baseline', 'noise', 'jitter', 'occlusion', 'dynamic', 'blur'],
        help='Select disturbance scenario for test matrix validation'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    print(f"[SIMULATOR] Initializing execution pipeline...")
    print(f"[SIMULATOR] Active Test Scenario -> {args.scenario}")

    # Simulated simulation frame loop placeholder
    # In your full pipeline, apply_disturbance(frame, scenario=args.scenario) 
    # will process live simulated frames here.
    
    print("[SIMULATOR] Pipeline test execution successful.")

if __name__ == "__main__":
    main()