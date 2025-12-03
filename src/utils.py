from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def load_flows(path: Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # timestamp normalization
    if 'ts' in df.columns:
        ts_col = 'ts'
    elif 'timestamp' in df.columns:
        ts_col = 'timestamp'
    else:
        df['ts'] = pd.to_datetime(pd.Series(pd.date_range("2000-01-01", periods=len(df), freq='s')))
        ts_col = 'ts'

    try:
        if not np.issubdtype(df[ts_col].dtype, np.datetime64):
            df['ts'] = pd.to_datetime(df[ts_col], errors='coerce')
            if df['ts'].isna().any():
                df['ts'] = pd.to_datetime(df[ts_col], errors='coerce')
    except Exception:
        df['ts'] = pd.to_datetime(df[ts_col], errors='coerce')

    if df['ts'].isna().all():
        df['ts'] = pd.to_datetime(pd.Series(pd.date_range("2000-01-01", periods=len(df), freq='s')))
    else:
        # use forward/backward fill methods directly to avoid FutureWarning
        df['ts'] = df['ts'].ffill().bfill()

    for col in ['row_id', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'proto', 'bytes', 'packets', 'duration', 'tcp_flags']:
        if col not in df.columns:
            df[col] = 0 if col in ('src_port', 'dst_port', 'bytes', 'packets', 'duration') else ''

    for ncol in ['src_port', 'dst_port', 'bytes', 'packets', 'duration']:
        df[ncol] = pd.to_numeric(df[ncol], errors='coerce').fillna(0).astype(float)

    if 'row_id' not in df.columns or df['row_id'].isnull().any():
        df['row_id'] = range(1, len(df) + 1)

    return df.sort_values('ts').reset_index(drop=True)


def basic_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    df = df.copy()
    # vectorized computations for performance on large dataframes
    duration = df['duration'].astype(float).replace([np.inf, -np.inf], 0).fillna(0)
    bytes_col = df['bytes'].astype(float).replace([np.inf, -np.inf], 0).fillna(0)
    packets_col = df['packets'].astype(float).replace([np.inf, -np.inf], 0).fillna(0)
    df['bytes_per_sec'] = np.where(duration > 0, bytes_col / duration, 0.0)
    df['pkts_per_sec'] = np.where(duration > 0, packets_col / duration, 0.0)
    df['byte_pkts_ratio'] = np.where(packets_col > 0, bytes_col / packets_col, 0.0)
    df['hour'] = df['ts'].dt.hour

    proto_dummies = pd.get_dummies(df['proto'].astype(str).fillna(''), prefix='proto')
    flags_dummies = pd.get_dummies(df['tcp_flags'].astype(str).fillna(''), prefix='flags')

    features = pd.concat([
        df[['row_id', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'bytes', 'packets', 'duration', 'bytes_per_sec', 'pkts_per_sec', 'byte_pkts_ratio', 'hour']],
        proto_dummies,
        flags_dummies
    ], axis=1)

    features = features.replace([np.inf, -np.inf], 0).fillna(0)
    categorical_cols = list(proto_dummies.columns) + list(flags_dummies.columns)
    return features, categorical_cols


@dataclass
class WindowStats:
    unique_dst_ports: int = 0
    connections_to_same_dst: int = 0
    outbound_bytes: float = 0.0
    inbound_bytes: float = 0.0
    beacon_cv: float = 0.0
    recent_count: int = 0


def windowed_host_features(df: pd.DataFrame, window_seconds: int = 60) -> pd.DataFrame:
    out_windows = defaultdict(deque)
    in_windows = defaultdict(deque)

    n = len(df)
    unique_dst_ports = np.zeros(n, dtype=float)
    connections_same_dst = np.zeros(n, dtype=float)
    outbound_bytes = np.zeros(n, dtype=float)
    inbound_bytes = np.zeros(n, dtype=float)
    beacon_cv = np.zeros(n, dtype=float)
    recent_count = np.zeros(n, dtype=float)

    def evict_deque(dq: deque, threshold_ts):
        while dq and dq[0][0] < threshold_ts:
            dq.popleft()

    for idx, row in df.reset_index().iterrows():
        ts_pd = pd.to_datetime(row['ts'])
        window_start = ts_pd - pd.Timedelta(seconds=window_seconds)
        src = row['src_ip']
        dst = row['dst_ip']
        dst_port = int(row.get('dst_port', 0)) if not pd.isna(row.get('dst_port', 0)) else 0
        b = float(row.get('bytes', 0.0))

        evict_deque(out_windows[src], window_start)
        evict_deque(in_windows[src], window_start)
        evict_deque(out_windows[dst], window_start)
        evict_deque(in_windows[dst], window_start)

        out_dq = out_windows[src]
        in_dq = in_windows[src]

        ports_set = {entry[1] for entry in out_dq}
        ports_set.add(dst_port)
        unique_dst_ports[idx] = float(len(ports_set))

        same_dst_count = sum(1 for entry in out_dq if entry[2] == dst) + 1
        connections_same_dst[idx] = float(same_dst_count)

        out_bytes_sum = sum(entry[3] for entry in out_dq) + b
        outbound_bytes[idx] = float(out_bytes_sum)

        in_bytes_sum = sum(entry[3] for entry in in_dq)
        inbound_bytes[idx] = float(in_bytes_sum)

        recent_count[idx] = float(len(out_dq) + 1)

        times = [entry[0] for entry in out_dq] + [ts_pd]
        if len(times) >= 3:
            diffs = np.diff(np.array([t.value for t in pd.to_datetime(times)]).astype('int64')) / 1e9
            beacon_cv[idx] = float(np.std(diffs) / np.mean(diffs)) if np.mean(diffs) > 0 else 0.0
        else:
            beacon_cv[idx] = 1.0

        out_windows[src].append((ts_pd, dst_port, dst, b))
        in_windows[dst].append((ts_pd, src, row.get('src_port', 0), b))

    winf = pd.DataFrame({
        'row_id': df['row_id'].values,
        'unique_dst_ports_window': unique_dst_ports,
        'connections_same_dst_window': connections_same_dst,
        'outbound_bytes_window': outbound_bytes,
        'inbound_bytes_window': inbound_bytes,
        'beacon_cv_window': beacon_cv,
        'recent_conn_count': recent_count,
    })

    winf = winf.replace([np.inf, -np.inf], 0).fillna(0)
    return winf


def assemble_features(df: pd.DataFrame, window_seconds: int = 60):
    basic_df, cat_cols = basic_features(df)
    # If source IP is missing or not useful (e.g., a single placeholder value),
    # skip per-host windowed features and use zeroed placeholders instead.
    try:
        src_present = 'src_ip' in df.columns and df['src_ip'].astype(str).nunique() > 1
    except Exception:
        src_present = False

    if not src_present:
        # create a zeroed window dataframe matching expected schema
        win_df = pd.DataFrame({
            'row_id': basic_df['row_id'].values,
            'unique_dst_ports_window': 0.0,
            'connections_same_dst_window': 0.0,
            'outbound_bytes_window': 0.0,
            'inbound_bytes_window': 0.0,
            'beacon_cv_window': 0.0,
            'recent_conn_count': 0.0,
        })
    else:
        win_df = windowed_host_features(df, window_seconds=window_seconds)

    merged = basic_df.merge(win_df, on='row_id', how='left')
    feature_cols = [c for c in merged.columns if c not in ('row_id', 'src_ip', 'dst_ip')]
    X = merged[feature_cols].replace([np.inf, -np.inf], 0).fillna(0)
    return X, feature_cols
