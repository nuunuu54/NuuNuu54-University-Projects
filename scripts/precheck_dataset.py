"""Pre-check dataset for required schema and basic class balance checks.

Usage:
  python scripts/precheck_dataset.py --input data/flows.csv --min-count 5

Exits with 0 on success, non-zero on fatal errors.
"""
from pathlib import Path
import argparse
import sys
import pandas as pd

REQUIRED_COLS = {'row_id','src_ip','dst_ip','src_port','dst_port','proto','bytes','packets','duration','tcp_flags'}
LABEL_CANDIDATES = ['label','class','attack','is_attack']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--min-count', type=int, default=5, help='Minimum examples per class to avoid warnings')
    args = p.parse_args()

    inp = Path(args.input)
    if not inp.exists():
        print('ERROR: input file not found:', inp)
        sys.exit(2)

    df = pd.read_csv(inp)
    cols = set([c.strip() for c in df.columns])
    missing = REQUIRED_COLS - cols
    if missing:
        print('ERROR: missing required columns:', missing)
        sys.exit(3)

    label_col = None
    for c in LABEL_CANDIDATES:
        if c in cols:
            label_col = c
            break
    if label_col is None:
        print('WARNING: no label column detected. Training will not be possible until you add a label column named one of:', LABEL_CANDIDATES)
    else:
        counts = df[label_col].astype(str).value_counts()
        print('Label distribution:')
        print(counts.to_string())
        small = counts[counts < args.min_count]
        if not small.empty:
            print('\nWARNING: these classes have fewer than', args.min_count, 'samples:')
            print(small.to_string())

    # check timestamp
    if 'ts' not in cols and 'timestamp' not in cols:
        print('NOTE: no timestamp column found; loader will synthesize monotonic timestamps.')

    print('\nPrecheck completed successfully')
    sys.exit(0)


if __name__ == '__main__':
    main()
