import os
import re
import pstats
import io
import subprocess
import argparse
import datetime
from pathlib import Path

# so can add this to bash script in one line and have changeable inputs, outputs, rmg locations
def parse_args():
    p = argparse.ArgumentParser(
        description='Analyze RMG YAML vs Chemkin writer performance'
    )
    p.add_argument(
        '--results-dir',
        required=True,
        help='Path to RMG output directory (e.g. results/gas_phase)'
    )
    p.add_argument(
        '--rmg-path',
        required=True,
        help='Path to RMG-Py installation (e.g. ~/RMG-Py)'
    )
    p.add_argument(
        '--output',
        required=True,
        help='Path to write the analysis report'
    )
    return p.parse_args()

# get RMG-Py git info, unchecked 
def get_rmg_git_info(rmg_path):
    def git(cmd):
        return subprocess.check_output(cmd, cwd=rmg_path, text=True).strip()
    return {
        'hash':    git(['git', 'rev-parse', 'HEAD']),
        'short':   git(['git', 'rev-parse', '--short', 'HEAD']),
        'message': git(['git', 'log', '-1', '--pretty=%s']),
        'branch':  git(['git', 'rev-parse', '--abbrev-ref', 'HEAD']),
        'date':    git(['git', 'log', '-1', '--pretty=%ci']),
    }

#finds the .profile file
def find_profile_file(results_dir):
    candidates = list(Path(results_dir).glob('*.profile'))
    if not candidates:
        print(f"  WARNING: No .profile file found in {results_dir}")
        return none
    #return the most recently modified one if multiple 
    return max(candidates, key=lambda file : file.stat().st_mtime)

#post-process profile data, focusing on comparing and summarizing the output writing methods (?)
#compare write times (cpu processing times)
#could also show where the program spends the most time and resources  
def process_profile_stats(profile_path):
    #profile path from find_profile_file()
    

#want to compare yaml and chemkin output to ensure that theyre the same
def compare(result_yaml, result_chemkin):
    #add compare logic 