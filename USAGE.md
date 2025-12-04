# Usage Guide

Complete reference for IDS-Tool commands with real-world examples.

## Table of Contents
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Training](#training)
- [Batch Inference](#batch-inference)
- [Streaming Inference](#streaming-inference)
- [Data Validation](#data-validation)
- [Data Normalization](#data-normalization)
- [Bulk Operations](#bulk-operations)
- [Advanced Features](#advanced-features)
- [Examples](#examples)

## Quick Start

### Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### First Command

```bash
# Check project setup
python -m IDS-tool.src.cli precheck

# Or use Windows wrapper
.\ids.ps1 precheck
```

## CLI Reference

All commands follow this pattern:

```bash
# Using Python module directly
python -m IDS-tool.src.cli <command> [options]

# Using wrapper (Windows)
.\ids.ps1 <command> [options]

# Using wrapper (Linux/Mac)
python -m IDS-tool.src.cli <command> [options]
```

## Training

### Basic Training

```bash
# Train on sample dataset
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --out models/my_model.pkl
```

**Parameters:**
- `--in`: Input CSV file (required)
- `--out`: Output model file path (required)
- `--feature-only`: Skip ML training, output features only
- `--sample`: Maximum rows to use (default: all)

### Advanced Training

```bash
# Train with limited rows (fast iteration)
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --out models/test.pkl \
  --sample 500

# Generate features without training
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --feature-only > features.json
```

### Model Output

Trained models are saved as pickle files containing:
- RandomForest classifier
- Feature column names
- Label encoder (if trained on labels)
- Window size and metadata

```python
import joblib
model_data = joblib.load('models/my_model.pkl')
print(model_data.keys())  # ['model', 'feature_columns', 'label_encoder', 'window_seconds']
```

## Batch Inference

Process entire CSV files for threat detection.

### Basic Batch Inference

```bash
# Run detection on CSV
python -m IDS-tool.src.cli batch \
  --in IDS-tool/data/flows.csv \
  --model models/my_model.pkl

# Save to JSON
python -m IDS-tool.src.cli batch \
  --in IDS-tool/data/flows.csv \
  --model models/my_model.pkl \
  --out detections.json
```

**Parameters:**
- `--in`: Input CSV file (required)
- `--model`: Trained model file (required)
- `--out`: Output JSON file (default: detections_batch.json)
- `--feature-only`: Output features without predictions

### Output Format

```json
{
  "metadata": {
    "timestamp": "2025-12-03T12:00:00Z",
    "model": "models/my_model.pkl",
    "total_flows": 100,
    "detections": 5
  },
  "detections": [
    {
      "row_index": 3,
      "src_ip": "192.168.1.10",
      "dst_ip": "10.0.0.1",
      "src_port": 54321,
      "dst_port": 80,
      "proto": "TCP",
      "heuristic_verdict": "port_scan",
      "heuristic_score": 0.92,
      "ml_prediction": "port_scan",
      "ml_confidence": 0.87,
      "combined_score": 0.95,
      "risk_level": "HIGH"
    },
    ...
  ]
}
```

## Streaming Inference

Process individual flows in real-time (one per line, JSON format).

### Basic Streaming

```bash
# Read from STDIN, output detections
python -m IDS-tool.src.cli stream \
  --model models/my_model.pkl \
  --out detections_stream.json
```

Then pipe JSON objects (one per line):

```bash
echo '{"src_ip":"192.168.1.10","dst_ip":"10.0.0.1","src_port":54321,"dst_port":80,"proto":"TCP","bytes":1024,"packets":10,"duration":5.5}'  | \
python -m IDS-tool.src.cli stream \
  --model models/my_model.pkl
```

### Streaming from File

```bash
# Simulate streaming from file
type detections_batch.json | python -m IDS-tool.src.cli stream --model models/my_model.pkl
```

**Expected Input (JSON):**
```json
{
  "src_ip": "192.168.1.10",
  "dst_ip": "10.0.0.1",
  "src_port": 54321,
  "dst_port": 80,
  "proto": "TCP",
  "bytes": 1024,
  "packets": 10,
  "duration": 5.5,
  "tcp_flags": "SYN"
}
```

**Output (per line):**
```json
{"src_ip":"192.168.1.10","verdict":"port_scan","confidence":0.95,"risk":"HIGH"}
```

## Data Validation

Validate CSV schema before training.

### Precheck Command

```bash
# Quick validation
python -m IDS-tool.src.cli precheck

# Check specific directory
python -m IDS-tool.src.cli precheck --dir IDS-tool/data
```

**Checks performed:**
- Required columns present: `src_ip`, `dst_ip`, `src_port`, `dst_port`, `proto`, `bytes`, `packets`, `duration`
- Data types valid
- Labels detected (if present)
- Class balance warnings
- File size warnings

**Output:**
```
Precheck Results:
  Total files: 1
  Valid files: 1
  Issues: 0
  Warnings: 1 (small classes detected)
  Recommended action: Run normalization if columns are non-standard
```

## Data Normalization

Map vendor-specific columns to IDS-Tool schema and handle missing IPs.

### Normalize Command

```bash
# Normalize all CSVs in directory
python -m IDS-tool.scripts.normalize_flows \
  --dir IDS-tool/data \
  --out-dir IDS-tool/data/normalized
```

**Parameters:**
- `--dir`: Input directory (required)
- `--out-dir`: Output directory (creates if not exists)

**Column Mapping (Auto-detected):**
- NetFlow: `src_ip` → `src_ip`, `src_port` → `src_port`
- Zeek: `id.orig_h` → `src_ip`, `id.orig_p` → `src_port`
- Custom variants: `srcip`, `source_ip`, `SourceIP` → `src_ip`

**Pseudo-IP Synthesis:**
When real IPs are missing, deterministic pseudo-IPs are generated:
```
MD5(filename) as seed → deterministic IP generation
Example: flows.csv → 192.168.0.1, 192.168.0.2, ... (consistent per run)
```

**Output Files:**
- `<original_name>.normalized.csv` in output directory
- All required columns present
- Consistent schema across all files

## Bulk Operations

Train models on multiple datasets automatically.

### Bulk Process

```bash
# Orchestrate: precheck + train + report
python -m IDS-tool.scripts.bulk_process \
  --dir IDS-tool/data/normalized
```

**Steps:**
1. Validates all CSV files
2. Trains RandomForest per file
3. Generates per-file JSON reports
4. Creates consolidated `bulk_report.json`

**Output:**
```
reports/
  ├── bulk_report.json                    # Consolidated summary
  ├── flows.normalized_train_report.json  # Per-file report
  └── ...
```

### Bulk Training Only

```bash
python -m IDS-tool.scripts.train_quick \
  --dir IDS-tool/data/normalized
```

**Generates:**
- Models in `models/rf_meta_*.pkl`
- Per-file reports in `reports/`
- Summary in `reports/train_quick_summary.json`

## Advanced Features

### Feature-Only Mode

Generate features without ML predictions (useful for feature inspection):

```bash
# Training (feature extraction)
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --feature-only > features.json

# Batch inference (features only)
python -m IDS-tool.src.cli batch \
  --in IDS-tool/data/flows.csv \
  --model models/my_model.pkl \
  --feature-only > features.json
```

### Hyperparameter Tuning

Fine-tune RandomForest for specific datasets:

```bash
# Run tuning (generates best_params.json)
python -m IDS-tool.src.tune_model \
  --in IDS-tool/data/flows.csv \
  --out best_params.json
```

### Data Merging

Combine multiple CSVs:

```bash
# Merge all CSVs in directory
python -m IDS-tool.scripts.ingest_merge \
  --input-dir IDS-tool/data/normalized \
  --output merged_flows.csv
```

## Examples

### Example 1: Train and Test on Sample Data

```bash
# Activate venv
.\.venv\Scripts\Activate.ps1

# Precheck
python -m IDS-tool.src.cli precheck

# Train model
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --out models/sample_model.pkl

# Run inference
python -m IDS-tool.src.cli batch \
  --in IDS-tool/data/flows.csv \
  --model models/sample_model.pkl \
  --out sample_detections.json

# View results
cat sample_detections.json | ConvertFrom-Json | Select-Object -ExpandProperty detections | Select-Object -First 5
```

### Example 2: Normalize and Bulk Train

```bash
# Normalize all data
python -m IDS-tool.scripts.normalize_flows \
  --dir IDS-tool/data \
  --out-dir IDS-tool/data/normalized

# Validate normalized data
python -m IDS-tool.src.cli precheck --dir IDS-tool/data/normalized

# Bulk process
python -m IDS-tool.scripts.bulk_process --dir IDS-tool/data/normalized

# View consolidated report
Get-Content reports/bulk_report.json | ConvertFrom-Json | Format-Table -AutoSize
```

### Example 3: Real-Time Streaming

```bash
# Terminal 1: Start streaming server (reads from STDIN)
python -m IDS-tool.src.cli stream \
  --model models/my_model.pkl \
  --out realtime_detections.json

# Terminal 2: Send flows (one per line)
Get-Content IDS-tool/data/flows.csv | ConvertFrom-Csv | ConvertTo-Json -AsArray | ForEach-Object { $_ | ConvertTo-Json } | Add-Content -Path flow_stream.json
cat flow_stream.json | python -m ...
```

### Example 4: Feature Inspection

```bash
# Extract features from dataset
python -m IDS-tool.src.cli train \
  --in IDS-tool/data/flows.csv \
  --feature-only | \
  ConvertFrom-Json | \
  Select-Object -ExpandProperty features | \
  Format-Table -AutoSize
```

## Tips & Tricks

### Optimize for Large Datasets

```bash
# Use sampling for quick iteration
python -m IDS-tool.src.cli train \
  --in large_dataset.csv \
  --out models/test.pkl \
  --sample 5000  # Limit to 5000 rows

# Validate on sample first
python -m IDS-tool.src.cli batch \
  --in large_dataset.csv \
  --model models/test.pkl \
  --out test_detections.json
```

### Monitor Training Progress

```bash
# Watch model training folder
Get-ChildItem models/ -Recurse | Sort-Object LastWriteTime | Select-Object -Last 10
```

### Parse Detection Output

```powershell
# Count detections by risk level
$detections = Get-Content detections_batch.json | ConvertFrom-Json
$detections.detections | Group-Object risk_level | Select-Object Name, Count
```

### Compare Models

```powershell
# Test multiple models on same data
foreach ($model in Get-ChildItem models/rf_*.pkl) {
  python -m IDS-tool.src.cli batch \
    --in IDS-tool/data/flows.csv \
    --model $model.FullName \
    --out "results_$($ model.BaseName).json"
}
```

## Troubleshooting CLI

### Command Not Found

```bash
# Ensure venv is activated
.\.venv\Scripts\Activate.ps1
python -m IDS-tool.src.cli --help
```

### File Not Found

```bash
# Check working directory
pwd  # Should be project root

# List available files
Get-ChildItem IDS-tool/data
```

### Permission Denied

```bash
# Set script execution policy (Windows)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Re-run command
.\ids.ps1 precheck
```

---

**More Help**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details or run `--help` on any command.
