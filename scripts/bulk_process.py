"""Bulk precheck and training for normalized datasets.

This script will:
 - iterate over `data/normalized/*.csv`
 - run a light schema check (using the same rules as precheck)
 - inspect `label` distribution and skip training if insufficient
 - train a model via `python -m src.train_model` for eligible files
 - save models to `models/rf_meta_<stem>.pkl` and logs to `reports/<stem>_train.txt`
 - write a consolidated JSON report to `reports/bulk_report.json`

Run with the project venv python for correct dependencies.
"""
from pathlib import Path
import subprocess
import json
import pandas as pd
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
DATA_N = ROOT / 'data' / 'normalized'
REPORTS = ROOT / 'reports'
MODELS = ROOT / 'models'
REPORTS.mkdir(exist_ok=True)
MODELS.mkdir(exist_ok=True)


def find_python():
    venv_py = ROOT.parent / '.venv' / 'Scripts' / 'python.exe'
    if venv_py.exists():
        return str(venv_py)
    return sys.executable or 'python'


def run_precheck(py, path):
    cmd = [py, 'scripts/precheck_dataset.py', '--input', str(path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def inspect_labels(path):
    try:
        df = pd.read_csv(path, nrows=100000)
    except Exception as e:
        return None, f'ERROR reading file: {e}'
    # detect label column
    lbl_cols = [c for c in df.columns if c.lower() in ('label','labels','attack','class')]
    if not lbl_cols:
        return None, 'no label column'
    lbl = lbl_cols[0]
    counts = df[lbl].value_counts().to_dict()
    return { 'label_col': lbl, 'counts': counts }, None


def train_model(py, path, out_model):
    cmd = [py, '-m', 'src.train_model', '--input', str(path), '--out', str(out_model), '--window', '60']
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main():
    py = find_python()
    files = sorted(DATA_N.glob('*.csv'))
    report = {'files': []}

    for f in files:
        entry = {'file': str(f), 'precheck': {}, 'inspect': {}, 'train': {}}
        try:
            rc, out, err = run_precheck(py, f)
            entry['precheck']['returncode'] = rc
            entry['precheck']['stdout'] = out.strip().splitlines()[-10:]
            entry['precheck']['stderr'] = err.strip().splitlines()[-10:]

            inspect_res, inspect_err = inspect_labels(f)
            if inspect_err:
                entry['inspect']['error'] = inspect_err
                report['files'].append(entry)
                continue
            entry['inspect'] = inspect_res

            counts = inspect_res['counts']
            # decide training eligibility: at least 2 classes and min 10 samples per class
            if len(counts) < 2 or min(counts.values()) < 10:
                entry['train']['skipped'] = True
                entry['train']['reason'] = 'insufficient class counts (need >=2 classes and >=10 samples per class)'
                report['files'].append(entry)
                continue

            out_model = MODELS / f'rf_meta_{f.stem}.pkl'
            rc_t, out_t, err_t = train_model(py, f, out_model)
            entry['train']['returncode'] = rc_t
            entry['train']['stdout'] = out_t.strip().splitlines()[-50:]
            entry['train']['stderr'] = err_t.strip().splitlines()[-50:]
            if rc_t == 0:
                entry['train']['model_path'] = str(out_model)
        except Exception as e:
            entry['error'] = repr(e)
            entry['traceback'] = traceback.format_exc()
        report['files'].append(entry)

    outp = REPORTS / 'bulk_report.json'
    with open(outp, 'w', encoding='utf8') as fh:
        json.dump(report, fh, indent=2)

    print('Bulk report written to', outp)


if __name__ == '__main__':
    main()
