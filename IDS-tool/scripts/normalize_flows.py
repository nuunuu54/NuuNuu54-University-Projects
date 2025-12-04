"""Normalize flow/pcap-derived CSVs to the project's canonical schema.

This script maps common exporter column names to the canonical contract and
writes normalized files to `data/normalized/<orig_name>.normalized.csv` by
default. When source/destination IPs are missing the normalizer will create
deterministic pseudo-IP addresses per-file so downstream windowed features and
heuristics continue to work.

Usage examples:
  python scripts/normalize_flows.py --dir data
  python scripts/normalize_flows.py --input data/some.csv --out-dir data/normalized
  python scripts/normalize_flows.py --dir data --out-dir data/normalized --mode aggressive
"""

from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import re
import hashlib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DEFAULT_OUT = DATA / 'normalized'

ALIASES = {
    'row_id': ['row_id', 'id', 'flow_id', 'uid', 'flowid'],
    'src_ip': ['src_ip', 'src ip', 'source_ip', 'srcaddr', 'src', 'sip', 'saddr'],
    'dst_ip': ['dst_ip', 'dst ip', 'destination_ip', 'dstaddr', 'dst', 'dip', 'daddr'],
    'src_port': ['src_port', 'src port', 'sport', 'source_port', 'srcport'],
    'dst_port': ['dst_port', 'dst port', 'dport', 'destination_port', 'dstport'],
    'proto': ['proto', 'protocol', 'prot', 'protocol_name'],
    'bytes': ['bytes', 'tot_len', 'total_length', 'total_bytes', 'flow_bytes'],
    'packets': ['packets', 'total_fwd_packets', 'total_bwd_packets', 'flow_packets', 'pkts'],
    'duration': ['duration', 'flow_duration', 'time', 'elapsed_time', 'dur'],
    'tcp_flags': ['tcp_flags', 'flags', 'tcpflag', 'tcp_flags_str', 'flow_flags'],
    'label': ['label', 'labels', 'attack', 'class', 'category', 'flow_label']
}

CANONICAL = ['row_id', 'ts', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'proto', 'bytes', 'packets', 'duration', 'tcp_flags', 'label']


def find_column(df_cols, candidates):
    df_cols_l = [c.lower() for c in df_cols]
    for cand in candidates:
        if cand.lower() in df_cols_l:
            idx = df_cols_l.index(cand.lower())
            return df_cols[idx]
    # try simplified match (strip non-alnum)
    simplified = {re.sub(r'[^0-9a-z]', '', c.lower()): c for c in df_cols}
    for cand in candidates:
        key = re.sub(r'[^0-9a-z]', '', cand.lower())
        if key in simplified:
            return simplified[key]
    # token substring heuristics
    for cand in candidates:
        tokens = [t for t in re.split(r'[_\\s]+', cand.lower()) if t]
        for col in df_cols:
            lc = col.lower()
            if all(tok in lc for tok in tokens):
                return col
    return None


def synthesize_ips_for_df(out: pd.DataFrame, filename: str):
    """Create deterministic pseudo IPs when real IPs are absent.

    Uses filename as salt so outputs are stable per-file.
    """
    salt = hashlib.md5(filename.encode()).hexdigest()
    base = int(salt[:8], 16)
    n = len(out)
    srcs = []
    dsts = []
    for i in range(n):
        v = (base + i) & 0xFFFFFF
        a = (v >> 16) & 0xFF
        b = (v >> 8) & 0xFF
        c = v & 0xFF
        a = (a % 250) + 1
        b = (b % 250) + 1
        c = (c % 250) + 1
        srcs.append(f'10.{a}.{b}.{c}')
        v2 = (base + i + 12345) & 0xFFFFFF
        a2 = ((v2 >> 16) & 0xFF) % 250 + 1
        b2 = ((v2 >> 8) & 0xFF) % 250 + 1
        c2 = (v2 & 0xFF) % 250 + 1
        dsts.append(f'10.{a2}.{b2}.{c2}')
    out['src_ip'] = srcs
    out['dst_ip'] = dsts


def normalize_df(df: pd.DataFrame, mode='conservative', filename: str = '') -> pd.DataFrame:
    out = pd.DataFrame()
    for canon, aliases in ALIASES.items():
        found = find_column(df.columns, aliases)
        if found is not None:
            out[canon] = df[found]

    # try to derive common numeric fields
    if 'bytes' not in out.columns:
        for candidate in ['total_length_of_fwd_packets', 'total_length_of_bwd_packets', 'total_length', 'total_bytes']:
            if candidate in df.columns:
                out['bytes'] = pd.to_numeric(df[candidate], errors='coerce').fillna(0)
                break

    if 'packets' not in out.columns:
        sum_cols = []
        for c in ['total_fwd_packets', 'total_bwd_packets', 'fwd_packets', 'bwd_packets', 'total_packets']:
            if c in df.columns:
                sum_cols.append(pd.to_numeric(df[c], errors='coerce').fillna(0))
        if sum_cols:
            out['packets'] = sum(sum_cols)

    if 'duration' not in out.columns:
        for candidate in ['flow_duration', 'duration_ms', 'elapsed_time']:
            if candidate in df.columns:
                out['duration'] = pd.to_numeric(df[candidate], errors='coerce').fillna(0)
                break

    if 'tcp_flags' not in out.columns:
        if 'flags' in df.columns:
            out['tcp_flags'] = df['flags'].astype(str)
        else:
            out['tcp_flags'] = ''

    if 'row_id' not in out.columns:
        out['row_id'] = range(1, len(df) + 1)

    if 'ts' not in out.columns:
        for c in df.columns:
            if 'time' in c.lower() or 'timestamp' in c.lower():
                try:
                    out['ts'] = pd.to_datetime(df[c], errors='coerce')
                    break
                except Exception:
                    continue
        if 'ts' not in out.columns:
            out['ts'] = pd.date_range('2020-01-01', periods=len(df), freq='S')

    if 'label' not in out.columns:
        lbl = find_column(df.columns, ALIASES['label'])
        if lbl:
            out['label'] = df[lbl]

    # If IPs missing, synthesize deterministic pseudo-IPs
    if 'src_ip' not in out.columns or 'dst_ip' not in out.columns:
        try:
            synthesize_ips_for_df(out, filename or '')
        except Exception:
            pass

    # reorder and sanitize types
    for c in CANONICAL:
        if c not in out.columns:
            out[c] = '' if c in ['tcp_flags', 'proto', 'label'] else 0

    out = out[CANONICAL]

    for n in ['bytes', 'packets', 'duration']:
        if n in out.columns:
            out[n] = pd.to_numeric(out[n], errors='coerce').fillna(0).replace([np.inf, -np.inf], 0)

    return out


def normalize_file(path: Path, out_dir: Path, mode='conservative') -> Path:
    print('Normalizing', path.name)
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print('  ERROR reading', path, e)
        return None
    norm = normalize_df(df, mode=mode, filename=path.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    outp = out_dir / (path.stem + '.normalized.csv')
    # Convert ts to string to avoid slow pandas datetime serialization
    if 'ts' in norm.columns:
        norm['ts'] = norm['ts'].astype(str)
    norm.to_csv(outp, index=False)
    missing = [c for c in ['row_id','src_ip','dst_ip','src_port','dst_port','proto','bytes','packets','duration','tcp_flags'] if c not in norm.columns]
    if missing:
        print('  WARNING: normalized file missing required columns:', missing)
    else:
        print('  OK: normalized file has required columns')
    return outp


def main():
    p = argparse.ArgumentParser(description='Normalize CSVs to canonical flow schema')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--input', help='Single CSV file to normalize')
    g.add_argument('--dir', help='Directory with CSVs to normalize')
    p.add_argument('--out-dir', help='Output directory', default=str(DEFAULT_OUT))
    p.add_argument('--mode', choices=['conservative','aggressive'], default='conservative')
    args = p.parse_args()

    out_dir = Path(args.out_dir) if Path(args.out_dir).is_absolute() else ROOT / args.out_dir

    if args.input:
        normalize_file(Path(args.input), out_dir, mode=args.mode)
        return

    d = Path(args.dir)
    csvs = list(d.glob('*.csv'))
    if not csvs:
        print('No CSVs found in', d)
        return
    for pth in csvs:
        if 'normalized' in pth.name:
            continue
        normalize_file(pth, out_dir, mode=args.mode)


if __name__ == '__main__':
    main()
"""Normalize various PCAP/flow CSV exports into the canonical flow schema used by the IDS.

This script does best-effort column mapping and light synthesis:
- maps common column name variants to canonical names
- coerces numeric columns (bytes, packets, ports, duration)
- synthesizes `row_id` and a monotonic `ts` if missing
- writes outputs to data/normalized/<orig_name>.normalized.csv

Usage:
  python scripts/normalize_flows.py --input data/SomeFile.csv
  python scripts/normalize_flows.py --dir data/ --out-dir data/normalized

This is conservative but will try to fill gaps; run the project's precheck after normalization.
"""
from pathlib import Path
import argparse
import pandas as pd
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT_DIR = DATA / 'normalized'


CANONICAL = ['row_id', 'ts', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'proto', 'bytes', 'packets', 'duration', 'tcp_flags', 'label']

# simple mapping keywords for canonical fields
MAPPINGS = {
    'row_id': ['row_id', 'id', 'flowid', 'flow_id'],
    'ts': ['ts', 'timestamp', 'time', 'flow_start', 'start_time', 'start'],
    'src_ip': ['src_ip', 'srcip', 'src address', 'saddr', 'sourceip', 'sip', 'srcaddr'],
    'dst_ip': ['dst_ip', 'dstip', 'dst address', 'daddr', 'dstaddr', 'dip', 'destip'],
    'src_port': ['src_port', 'sport', 'srcport', 'source_port'],
    'dst_port': ['dst_port', 'dport', 'dstport', 'dest_port'],
    'proto': ['proto', 'protocol', 'protocol_name'],
    'bytes': ['bytes', 'tot_bytes', 'total_bytes', 'bytessent', 'flow_bytes'],
    'packets': ['packets', 'pkts', 'flow_packets', 'total_packets'],
    'duration': ['duration', 'flow_duration', 'dur', 'elapsed'],
    'tcp_flags': ['tcp_flags', 'flags', 'tcpflag', 'flow_flags'],
    'label': ['label', 'class', 'attack', 'malicious', 'traffic_type']
}


def normalize_columns(df: pd.DataFrame):
    # build lowercase simplified map of existing columns
    col_map = {}
    norm_names = {c: re.sub(r'[^a-z0-9]', '', c.lower()) for c in df.columns}
    used = set()
    for canon, variants in MAPPINGS.items():
        found = None
        for v in variants:
            vnorm = re.sub(r'[^a-z0-9]', '', v.lower())
            # direct match on simplified name
            for col, sn in norm_names.items():
                if sn == vnorm:
                    found = col
                    break
            if found:
                break
        # if not found, try contains match
        if not found:
            for col, sn in norm_names.items():
                for v in variants:
                    vnorm = re.sub(r'[^a-z0-9]', '', v.lower())
                    if vnorm in sn and col not in used:
                        found = col
                        break
                if found:
                    break
        if found:
            col_map[found] = canon
            used.add(found)

    # Rename found columns
    df = df.rename(columns=col_map)
    return df


def coerce_types(df: pd.DataFrame):
    # create row_id if missing
    if 'row_id' not in df.columns:
        df.insert(0, 'row_id', range(1, len(df) + 1))

    # synthesize ts if missing
    if 'ts' not in df.columns:
        # use lowercase 's' frequency to avoid FutureWarning
        df['ts'] = pd.date_range(start='2000-01-01', periods=len(df), freq='s')

    # numeric coercions
    for col in ['src_port', 'dst_port']:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce')
            s = s.replace([np.inf, -np.inf], 0).fillna(0)
            df[col] = s.astype(int)

    for col in ['bytes', 'packets']:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors='coerce')
            s = s.replace([np.inf, -np.inf], 0).fillna(0)
            df[col] = s.astype(int)
        else:
            df[col] = 0

    if 'duration' in df.columns:
        s = pd.to_numeric(df['duration'], errors='coerce')
        s = s.replace([np.inf, -np.inf], 0).fillna(0.0)
        df['duration'] = s
    else:
        df['duration'] = 0.0

    # tcp_flags: stringify
    if 'tcp_flags' in df.columns:
        df['tcp_flags'] = df['tcp_flags'].astype(str)
    else:
        df['tcp_flags'] = ''

    # proto ensure string
    if 'proto' in df.columns:
        df['proto'] = df['proto'].astype(str)
    else:
        df['proto'] = ''

    return df


def normalize_file(path: Path, out_dir: Path):
    print(f'Normalizing: {path.name}')
    df = pd.read_csv(path)
    df = normalize_columns(df)
    df = coerce_types(df)

    # ensure canonical order, add missing canonical cols
    for c in CANONICAL:
        if c not in df.columns:
            df[c] = '' if c in ['tcp_flags', 'proto', 'label'] else 0

    df = df[CANONICAL]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (path.stem + '.normalized.csv')
    df.to_csv(out_path, index=False)
    print(f'Wrote normalized: {out_path}')
    return out_path


def main():
    p = argparse.ArgumentParser(description='Normalize PCAP/flow CSVs to canonical flow schema')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--input', help='Single input CSV file path')
    g.add_argument('--dir', help='Directory with CSVs to normalize')
    p.add_argument('--out-dir', help='Output directory (inside data/) relative to project root', default=str(OUT_DIR))
    args = p.parse_args()

    out_dir = Path(args.out_dir) if Path(args.out_dir).is_absolute() else ROOT / args.out_dir
    if args.input:
        in_path = Path(args.input)
        normalize_file(in_path, out_dir)
        return

    d = Path(args.dir)
    csvs = list(d.glob('*.csv'))
    if not csvs:
        print('No CSVs found in', d)
        return
    for pth in csvs:
        normalize_file(pth, out_dir)


if __name__ == '__main__':
    main()
