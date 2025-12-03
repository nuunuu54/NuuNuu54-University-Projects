"""Quick trainer for normalized CSVs: trains small RandomForest per file and saves models+logs.

Usage:
  python scripts/train_quick.py --input data/normalized/XXX.normalized.csv
  python scripts/train_quick.py --all
"""
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import sys

# Ensure project root is on sys.path so `from src...` imports work when running this script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import json

DATA_N = ROOT / 'data' / 'normalized'
MODELS = ROOT / 'models'
REPORTS = ROOT / 'reports'
MODELS.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

def assemble_from_src():
    from src.utils import load_flows, assemble_features
    return load_flows, assemble_features


def train_file(path: Path, n_estimators=20, max_depth=8, window=60):
    lf, assemble = assemble_from_src()
    # For large CSVs, only read a sample to keep training fast
    fsize = path.stat().st_size
    if fsize > 20 * 1024 * 1024:
        # large file: read first N rows and normalize via ids.load_flows_from_df
        import pandas as _pd
        raw = _pd.read_csv(path, nrows=50000)
        try:
            from src.ids import load_flows_from_df
            df = load_flows_from_df(raw)
        except Exception:
            # fallback to load_flows on full file (may be slow)
            df = lf(path)
    else:
        df = lf(path)
    # find label
    label_col = None
    for c in ('label','class','attack','is_attack'):
        if c in df.columns:
            label_col = c
            break
    report = {'file': str(path), 'trained': False}
    if label_col is None:
        report['error'] = 'no label column'
        return report
    X, cols = assemble(df, window_seconds=window)
    y = df[label_col].astype(str)
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    if len(np.unique(y_enc)) < 2:
        report['error'] = 'single-class'
        return report
    if y_enc.size < 20:
        report['warning'] = 'very small dataset'
    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.25, stratify=y_enc if len(np.unique(y_enc))>1 else None, random_state=42)
    clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, class_weight='balanced_subsample', random_state=42, n_jobs=1)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    cr = classification_report(y_test, preds, zero_division=0, output_dict=True)
    out_model = MODELS / f'rf_meta_{path.stem}.pkl'
    meta = {'model': clf, 'feature_columns': cols, 'label_encoder': le, 'window_seconds': window}
    joblib.dump(meta, out_model)
    report.update({'trained': True, 'model_path': str(out_model), 'metrics': cr})
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input')
    p.add_argument('--all', action='store_true')
    p.add_argument('--n-est', type=int, default=20)
    p.add_argument('--max-depth', type=int, default=8)
    p.add_argument('--window', type=int, default=60)
    args = p.parse_args()
    files = []
    if args.input:
        files = [Path(args.input)]
    elif args.all:
        files = sorted(DATA_N.glob('*.csv'))
    else:
        print('Specify --input or --all')
        return
    reports = []
    for f in files:
        print('Training on', f.name)
        try:
            r = train_file(f, n_estimators=args.n_est, max_depth=args.max_depth, window=args.window)
        except Exception as e:
            r = {'file': str(f), 'error': str(e)}
        reports.append(r)
        # save per-file report
        rp = REPORTS / f'{f.stem}_train_report.json'
        with open(rp, 'w', encoding='utf8') as fh:
            json.dump(r, fh, indent=2)
    # consolidated
    outp = REPORTS / 'train_quick_summary.json'
    with open(outp, 'w', encoding='utf8') as fh:
        json.dump({'results': reports}, fh, indent=2)
    print('Training summary written to', outp)


if __name__ == '__main__':
    main()
