import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
MODELS_DIR = ROOT / 'models'


def find_input_file():
    # Prefer canonical merged file, else pick the largest CSV in data/
    merged = DATA_DIR / 'merged_flows.csv'
    if merged.exists():
        return str(merged)
    csvs = list(DATA_DIR.glob('*.csv'))
    if not csvs:
        raise FileNotFoundError(f'No CSV files found in {DATA_DIR}')
    # pick largest file
    csvs.sort(key=lambda p: p.stat().st_size, reverse=True)
    return str(csvs[0])


def find_python_executable():
    # Prefer project venv if present
    venv_py = ROOT.parent / '.venv' / 'Scripts' / 'python.exe'
    if venv_py.exists():
        return str(venv_py)
    return sys.executable or 'python'


def run_module(module_name, args_list):
    py = find_python_executable()
    cmd = [py, '-m', module_name] + args_list
    print('Running:', ' '.join(cmd))
    return subprocess.run(cmd)


def cmd_train(args):
    input_path = args.input or find_input_file()
    MODELS_DIR.mkdir(exist_ok=True)
    out = args.out or str(MODELS_DIR / 'rf_meta.pkl')
    cmd_args = ['--input', input_path, '--out', out, '--window', str(args.window or 60)]
    if args.extra:
        cmd_args += args.extra
    return run_module('src.train_model', cmd_args)


def cmd_batch(args):
    input_path = args.input or find_input_file()
    model = args.model or str(MODELS_DIR / 'rf_meta.pkl')
    cmd_args = ['--input', input_path, '--model', model, '--mode', 'batch']
    if args.extra:
        cmd_args += args.extra
    return run_module('src.ids', cmd_args)


def cmd_stream(args):
    input_path = args.input or find_input_file()
    model = args.model or str(MODELS_DIR / 'rf_meta.pkl')
    cmd_args = ['--input', input_path, '--model', model, '--mode', 'stream']
    if args.extra:
        cmd_args += args.extra
    return run_module('src.ids', cmd_args)


def cmd_precheck(args):
    input_path = args.input or find_input_file()
    cmd = [find_python_executable(), 'scripts/precheck_dataset.py', '--input', input_path]
    if args.extra:
        cmd += args.extra
    print('Running:', ' '.join(cmd))
    return subprocess.run(cmd)


def cmd_merge(args):
    # Call the ingest_merge script which lives in scripts/
    cmd = [find_python_executable(), 'scripts/ingest_merge.py']
    if args.extra:
        cmd += args.extra
    print('Running:', ' '.join(cmd))
    return subprocess.run(cmd)


def cmd_tune(args):
    input_path = args.input or find_input_file()
    out = args.out or str(MODELS_DIR / 'rf_meta_tuned.pkl')
    cmd_args = ['--input', input_path, '--out', out]
    if args.extra:
        cmd_args += args.extra
    return run_module('src.tune_model', cmd_args)


def cmd_e2e(args):
    cmd = [find_python_executable(), 'scripts/run_e2e.py']
    if args.extra:
        cmd += args.extra
    print('Running:', ' '.join(cmd))
    return subprocess.run(cmd)


def main():
    p = argparse.ArgumentParser(prog='ids', description='Simple IDS one-word CLI wrapper')
    sp = p.add_subparsers(dest='cmd')

    p_train = sp.add_parser('train', help='Train model (picks CSV from data/)')
    p_train.add_argument('--input', help='Path to input CSV')
    p_train.add_argument('--out', help='Output model metadata path')
    p_train.add_argument('--window', type=int, help='Window seconds for features')
    p_train.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to train module', default=None)

    p_batch = sp.add_parser('batch', help='Run batch inference')
    p_batch.add_argument('--input', help='Input CSV')
    p_batch.add_argument('--model', help='Model metadata path')
    p_batch.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to ids module', default=None)

    p_stream = sp.add_parser('stream', help='Run streaming inference (simulated)')
    p_stream.add_argument('--input', help='Input CSV')
    p_stream.add_argument('--model', help='Model metadata path')
    p_stream.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to ids module', default=None)

    p_pre = sp.add_parser('precheck', help='Validate dataset schema and class counts')
    p_pre.add_argument('--input', help='Input CSV')
    p_pre.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to precheck script', default=None)

    p_merge = sp.add_parser('merge', help='Merge multiple CSVs into canonical file')
    p_merge.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to ingest_merge', default=None)

    p_tune = sp.add_parser('tune', help='Run hyperparameter tuning')
    p_tune.add_argument('--input', help='Input CSV')
    p_tune.add_argument('--out', help='Output tuned model path')
    p_tune.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to tune module', default=None)

    p_e2e = sp.add_parser('e2e', help='Run end-to-end runner')
    p_e2e.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to e2e runner', default=None)

    p_bulk = sp.add_parser('bulk-train', help='Run quick bulk training over normalized datasets')
    p_bulk.add_argument('--n-est', type=int, help='Number of trees for quick training')
    p_bulk.add_argument('--max-depth', type=int, help='Max depth for quick training')
    p_bulk.add_argument('--window', type=int, help='Window seconds for features')
    p_bulk.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to train_quick', default=None)

    p_report = sp.add_parser('bulk-report', help='Run consolidated precheck+report (bulk_process)')
    p_report.add_argument('extra', nargs=argparse.REMAINDER, help='Extra args forwarded to bulk_process', default=None)

    args = p.parse_args()

    if args.cmd == 'train':
        return cmd_train(args)
    if args.cmd == 'batch':
        return cmd_batch(args)
    if args.cmd == 'stream':
        return cmd_stream(args)
    if args.cmd == 'precheck':
        return cmd_precheck(args)
    if args.cmd == 'merge':
        return cmd_merge(args)
    if args.cmd == 'tune':
        return cmd_tune(args)
    if args.cmd == 'e2e':
        return cmd_e2e(args)
    if args.cmd == 'bulk-train':
        # build args for train_quick
        cmd = [find_python_executable(), 'scripts/train_quick.py', '--all']
        if args.n_est:
            cmd += ['--n-est', str(args.n_est)]
        if args.max_depth:
            cmd += ['--max-depth', str(args.max_depth)]
        if args.window:
            cmd += ['--window', str(args.window)]
        if args.extra:
            cmd += args.extra
        print('Running:', ' '.join(cmd))
        return subprocess.run(cmd)
    if args.cmd == 'bulk-report':
        cmd = [find_python_executable(), 'scripts/bulk_process.py']
        if args.extra:
            cmd += args.extra
        print('Running:', ' '.join(cmd))
        return subprocess.run(cmd)

    p.print_help()
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
