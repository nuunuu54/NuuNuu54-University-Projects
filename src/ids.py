"""Minimal IDS inference engine supporting batch and streaming modes.
"""
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

import joblib
import numpy as np
import pandas as pd

from src.utils import load_flows, assemble_features

# simple heuristics
PORT_SCAN_UNIQUE_PORTS = 20
BRUTE_FORCE_CONN_THRESHOLD = 50
EXFILTRATION_BYTES_THRESHOLD = 1_000_000
EXFILTRATION_RATIO = 10.0
BEACON_CV_THRESHOLD = 0.2
BEACON_MIN_COUNT = 5


def load_model(model_path: Path):
    m = joblib.load(model_path)
    if isinstance(m, dict):
        return m
    return {'model': m, 'feature_columns': None, 'label_encoder': None, 'window_seconds': 60}


def apply_heuristics(row_features: Dict[str, Any]) -> List[Dict[str, Any]]:
    detections = []
    up = float(row_features.get('unique_dst_ports_window', 0))
    if up >= PORT_SCAN_UNIQUE_PORTS:
        detections.append({'reason': 'Port_Scan_Rule', 'score': min(1.0, up / (PORT_SCAN_UNIQUE_PORTS * 2)), 'class_guess': 'port_scan', 'explain': {'unique_ports': up}})
    bf = float(row_features.get('connections_same_dst_window', 0))
    if bf >= BRUTE_FORCE_CONN_THRESHOLD:
        detections.append({'reason': 'Brute_Force_Rule', 'score': min(1.0, bf / (BRUTE_FORCE_CONN_THRESHOLD * 2)), 'class_guess': 'brute_force', 'explain': {'connections_to_same_dst': bf}})
    outb = float(row_features.get('outbound_bytes_window', 0))
    inb = float(row_features.get('inbound_bytes_window', 0))
    if (outb >= EXFILTRATION_BYTES_THRESHOLD) or (outb / (inb + 1.0) >= EXFILTRATION_RATIO):
        detections.append({'reason': 'Exfiltration_Rule', 'score': 1.0, 'class_guess': 'exfiltration', 'explain': {'outbound_bytes': outb, 'inbound_bytes': inb}})
    cv = float(row_features.get('beacon_cv_window', 1.0))
    cnt = float(row_features.get('recent_conn_count', 0))
    if (cv <= BEACON_CV_THRESHOLD) and (cnt >= BEACON_MIN_COUNT):
        detections.append({'reason': 'Beaconing_Rule', 'score': min(1.0, (BEACON_MIN_COUNT / max(1.0, cnt)) * (1.0 - cv)), 'class_guess': 'beaconing', 'explain': {'beacon_cv': cv, 'recent_count': cnt}})
    return detections


def run_batch(input_path: Path, model_meta: dict) -> List[Dict[str, Any]]:
    df = load_flows(input_path)
    X, feature_cols = assemble_features(df, window_seconds=int(model_meta.get('window_seconds', 60)))
    model_cols = model_meta.get('feature_columns', feature_cols)
    for c in model_cols:
        if c not in X.columns:
            X[c] = 0.0
    X = X[model_cols]
    clf = model_meta['model']
    label_encoder = model_meta.get('label_encoder', None)

    try:
        proba = clf.predict_proba(X)
    except Exception:
        proba = None

    dets = []
    for i, row in df.reset_index().iterrows():
        row_id = int(row['row_id'])
        rf = X.iloc[i].to_dict()
        heur = apply_heuristics(rf)
        ml_det = []
        if proba is not None:
            try:
                probs = proba[i]
                top_idx = int(np.argmax(probs))
                top_prob = float(probs[top_idx])
                class_guess = label_encoder.classes_[top_idx] if label_encoder is not None else str(top_idx)
                if top_prob >= 0.5:
                    ml_det.append({'reason': 'ML_Detection', 'score': top_prob, 'class_guess': str(class_guess), 'explain': {'ml_probabilities': probs.tolist()}})
            except Exception:
                pass
        for d in (heur + ml_det):
            dets.append({'row_id': row_id, 'reason': d['reason'], 'score': float(d['score']), 'class_guess': d['class_guess'], 'explain': d['explain']})
    return dets


def run_streaming(input_path: Path, model_meta: dict, delay: float = 0.001) -> List[Dict[str, Any]]:
    clf = model_meta['model']
    model_cols = model_meta.get('feature_columns', None)
    label_encoder = model_meta.get('label_encoder', None)
    window_seconds = int(model_meta.get('window_seconds', 60))

    buffer_rows = []
    dets = []
    for chunk in pd.read_csv(input_path, chunksize=1):
        try:
            df_row = chunk.copy()
            if 'ts' not in df_row.columns and 'timestamp' in df_row.columns:
                df_row['ts'] = pd.to_datetime(df_row['timestamp'], errors='coerce')
            elif 'ts' not in df_row.columns:
                df_row['ts'] = pd.Timestamp.now()
            buffer_rows.append(df_row.iloc[0].to_dict())
            buf_df = pd.DataFrame(buffer_rows)
            buf_df = buf_df.reset_index(drop=True)
            buf_norm = load_flows_from_df(buf_df)
            X_buf, feature_cols_buf = assemble_features(buf_norm, window_seconds=window_seconds)
            last_idx = X_buf.shape[0] - 1
            if last_idx < 0:
                continue
            rf = X_buf.iloc[last_idx].to_dict()
            heur = apply_heuristics(rf)
            ml_det = []
            try:
                if model_cols is not None:
                    for c in model_cols:
                        if c not in X_buf.columns:
                            X_buf[c] = 0.0
                    X_al = X_buf[model_cols]
                else:
                    X_al = X_buf
                probs = clf.predict_proba(X_al)
                probs_last = probs[last_idx]
                top_idx = int(np.argmax(probs_last))
                top_prob = float(probs_last[top_idx])
                class_guess = label_encoder.classes_[top_idx] if label_encoder is not None else str(top_idx)
                if top_prob >= 0.5:
                    ml_det.append({'reason': 'ML_Detection', 'score': top_prob, 'class_guess': str(class_guess), 'explain': {'ml_probabilities': probs_last.tolist()}})
            except Exception:
                ml_det = []
            latest_row = buf_df.iloc[-1]
            row_id = int(latest_row.get('row_id', -1)) if 'row_id' in latest_row else -1
            for d in (heur + ml_det):
                dets.append({'row_id': row_id, 'reason': d['reason'], 'score': float(d['score']), 'class_guess': d['class_guess'], 'explain': d['explain']})
            latest_ts = pd.to_datetime(latest_row.get('ts'))
            new_buf = [r for r in buffer_rows if pd.to_datetime(r.get('ts')) >= (latest_ts - pd.Timedelta(seconds=window_seconds))]
            buffer_rows = new_buf
        except Exception:
            continue
    return dets


def load_flows_from_df(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    if 'ts' in df2.columns:
        df2['ts'] = pd.to_datetime(df2['ts'], errors='coerce')
    elif 'timestamp' in df2.columns:
        df2['ts'] = pd.to_datetime(df2['timestamp'], errors='coerce')
    else:
        df2['ts'] = pd.to_datetime(pd.Series(pd.date_range("2000-01-01", periods=len(df2), freq='S')))
    for col in ['row_id', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'proto', 'bytes', 'packets', 'duration', 'tcp_flags']:
        if col not in df2.columns:
            df2[col] = 0 if col in ('src_port','dst_port','bytes','packets','duration') else ''
    for ncol in ['src_port', 'dst_port', 'bytes', 'packets', 'duration']:
        df2[ncol] = pd.to_numeric(df2[ncol], errors='coerce').fillna(0).astype(float)
    if 'row_id' not in df2.columns or df2['row_id'].isnull().any():
        df2['row_id'] = range(1, len(df2) + 1)
    return df2.sort_values('ts').reset_index(drop=True)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--mode', choices=['batch', 'streaming'], default='batch')
    p.add_argument('--model', required=True)
    p.add_argument('--feature-only', action='store_true', help='Run in feature-only mode (disable windowed host features)')
    args = p.parse_args()
    inp = Path(args.input)
    if not inp.exists():
        raise SystemExit(f'Input file not found: {inp}')
    model_meta = load_model(Path(args.model))
    if args.feature_only:
        model_meta['window_seconds'] = 0
    if args.mode == 'batch':
        dets = run_batch(inp, model_meta)
    else:
        dets = run_streaming(inp, model_meta)
    print(json.dumps(dets))


if __name__ == '__main__':
    main()
