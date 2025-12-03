# IDS ML Pipeline
# IDS ML Pipeline

This repository contains a hybrid IDS with feature engineering, training, batch and streaming
inference, and simple heuristics.

**Required CSV schema (contract)**
- `row_id` (int)
- `src_ip`, `dst_ip` (strings)
- `src_port`, `dst_port` (numeric)
- `proto` (string)
- `bytes`, `packets`, `duration` (numeric)
- `tcp_flags` (string)
- `timestamp` or `ts` (optional): ISO timestamp or epoch seconds. If missing, timestamps may be synthesized.
- `label` (recommended for training): named class (e.g., `benign`, `port_scan`, `brute_force`, `exfiltration`, `beaconing`). The trainer accepts columns named `label`, `class`, `attack`, or `is_attack`.

**Quick usage (PowerShell, from project root)**

- Run training (venv python recommended):
	- `& '.\.venv\Scripts\python.exe' -m src.train_model --input data/flows.csv --out models/rf_meta.pkl --window 60`
- Batch inference:
	- `& '.\.venv\Scripts\python.exe' -m src.ids --input data/flows.csv --mode batch --model models/rf_meta.pkl > detections_batch.json`
- Streaming inference (simulated delay):
	- `& '.\.venv\Scripts\python.exe' -m src.ids --input data/flows.csv --mode streaming --model models/rf_meta.pkl > detections_stream.json`
- Precheck a dataset file:
	- `& '.\.venv\Scripts\python.exe' scripts\precheck_dataset.py --input data/flows.csv --min-count 5`

**CLI wrapper**
- One-word CLI is available via `src/cli.py` and `ids.bat` / `ids.ps1` on Windows.
- Commands include: `train`, `batch`, `stream`, `precheck`, `merge`, `tune`, `e2e`, `bulk-train`, `bulk-report`.

**Normalizer behavior**
- Run the normalizer: `& '.\.venv\Scripts\python.exe' scripts\normalize_flows.py --input data --out data/normalized`
- The normalizer maps many exporter-specific column names into the canonical contract. When `src_ip`/`dst_ip` are absent the normalizer now synthesizes deterministic pseudo-IP addresses per-file so windowed host features and heuristics still work. This synthesis is deterministic and only used when real IPs are missing.

**Notes & recommendations**
- Always use the project venv Python to avoid environment/package mismatches: `.venv\Scripts\python.exe`.
- For effective ML models, provide many labeled flows per class (hundreds to thousands) and ensure labels are representative. The trainer will skip files without a usable label column or with only a single-class.
- Model artifacts are saved under `models/` and include metadata: `model`, `feature_columns`, `label_encoder`, `window_seconds`.

**Safest way to push changes to GitHub (recommended)**
Run these commands in PowerShell from the project root (replace `<your-remote>` with your repo URL):

```
git add -A
git commit -m "Finish normalization + pseudo-IP synth + README"
git branch -M IDS
git remote add origin <your-remote>
git push -u origin IDS
```

If you want me to push directly, provide the remote URL and a PAT and confirm; otherwise run the commands above locally.

If you want a custom normalization mapping for a specific CSV, tell me the filename and I will inspect its header and implement a targeted mapping and re-run normalization + precheck + quick-train for that file.
