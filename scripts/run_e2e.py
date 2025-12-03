"""Run a quick end-to-end: train -> batch infer -> streaming infer (writes artifacts)."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / '.venv' / 'Scripts' / 'python.exe'
MODEL = ROOT / 'models' / 'rf_meta.pkl'
DATA = ROOT / 'data' / 'flows.csv'

# Train
print('Training...')
subprocess.run([str(PY), '-m', 'src.train_model', '--input', str(DATA), '--out', str(MODEL)], check=True)

# Batch infer
print('Batch infer...')
with open(ROOT / 'detections_batch.json', 'w') as f:
    subprocess.run([str(PY), '-m', 'src.ids', '--input', str(DATA), '--mode', 'batch', '--model', str(MODEL)], stdout=f, check=True)

# Streaming infer
print('Streaming infer...')
with open(ROOT / 'detections_stream.json', 'w') as f:
    subprocess.run([str(PY), '-m', 'src.ids', '--input', str(DATA), '--mode', 'streaming', '--model', str(MODEL)], stdout=f, check=True)

print('E2E done')
