"""Merge multiple flow CSVs into a canonical `data/merged_flows.csv` with schema normalization.

Usage:
  python scripts/ingest_merge.py --inputs data/a.csv data/b.csv --out data/merged_flows.csv
  python scripts/ingest_merge.py --indir ./downloads --out data/merged_flows.csv

The script will:
- Read CSVs robustly
- Ensure required columns exist (fill missing with defaults)
- Normalize column names
- Remove exact duplicate rows
- Optionally sort by timestamp
"""
from pathlib import Path
import argparse
import pandas as pd

REQUIRED = ['row_id','src_ip','dst_ip','src_port','dst_port','proto','bytes','packets','duration','tcp_flags']


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    for col in REQUIRED:
        if col not in df.columns:
            df[col] = 0 if col in ('src_port','dst_port','bytes','packets','duration') else ''
    # ensure numeric casting
    for n in ('src_port','dst_port','bytes','packets','duration'):
        df[n] = pd.to_numeric(df[n], errors='coerce').fillna(0)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', nargs='*', help='List of CSV files to merge')
    p.add_argument('--indir', help='Directory to read all CSV files from')
    p.add_argument('--out', required=True, help='Output merged CSV path')
    p.add_argument('--sort', action='store_true', help='Sort output by timestamp if available (ts or timestamp)')
    args = p.parse_args()

    paths = []
    if args.inputs:
        paths += [Path(p) for p in args.inputs]
    if args.indir:
        d = Path(args.indir)
        if d.exists():
            paths += list(d.glob('*.csv'))

    if not paths:
        raise SystemExit('No input files found')

    dfs = []
    for p in paths:
        try:
            dfi = pd.read_csv(p)
            dfi = normalize_df(dfi)
            dfs.append(dfi)
        except Exception as e:
            print('Warning: failed to read', p, e)
            continue

    if not dfs:
        raise SystemExit('No valid CSVs to merge')

    merged = pd.concat(dfs, ignore_index=True)
    merged = merged.drop_duplicates()

    if args.sort:
        if 'ts' in merged.columns:
            merged['ts'] = pd.to_datetime(merged['ts'], errors='coerce')
            merged = merged.sort_values('ts')
        elif 'timestamp' in merged.columns:
            merged['ts'] = pd.to_datetime(merged['timestamp'], errors='coerce')
            merged = merged.sort_values('ts')

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(outp, index=False)
    print('Wrote merged CSV to', outp)


if __name__ == '__main__':
    main()
