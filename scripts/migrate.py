#!/usr/bin/env python3
"""
migrate.py — One-click migration from multi-store to unified MemPalace.
Usage: python3 migrate.py [--phase backup|migrate|clean|index|fix|verify] [--all]
"""
import argparse, os, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['backup','migrate','clean','index','fix','verify'])
    parser.add_argument('--all', action='store_true', help='Run all phases')
    args = parser.parse_args()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    phases = [
        ('backup', 'migration-backup.py', 'Phase 1: Backup everything'),
        ('migrate', 'migration-phase2.py', 'Phase 2: Migrate Light Memory'),
        ('clean', None, 'Phase 3: Clean test data (skipped, harmless)'),
        ('index', 'migration-phase4.py', 'Phase 4: Index wiki pages'),
        ('fix', None, 'Phase 5: Fix infra (run manually)'),
        ('verify', 'deep-flow-test.py', 'Phase 6: Verify'),
    ]
    
    if args.all:
        for phase_name, script, desc in phases:
            if script:
                print(f"\n{'='*50}")
                print(f"Running: {desc}")
                print(f"{'='*50}")
                os.system(f"python3 {os.path.join(script_dir, script)}")
    elif args.phase:
        for phase_name, script, desc in phases:
            if phase_name == args.phase and script:
                print(f"Running: {desc}")
                os.system(f"python3 {os.path.join(script_dir, script)}")
                break
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
