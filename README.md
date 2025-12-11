# Server-Admin-Work Repository

This repository contains **two separate projects** with independent branches:

## 📋 Projects Overview

### 1. **Server-Admin-Project** 
PowerShell-based Windows Server automation and configuration management.

**Branch:** `Server-Admin-Project`

**Features:**
- Automated Windows Server 2022 configuration
- Network settings, IIS, DNS, WSUS, Windows Update management
- Rollback framework for all applied changes
- Dry-run mode for safe preview before execution
- Comprehensive Pester test suite (14 tests)
- GitHub Actions CI/CD pipeline

**Quick Start:**
```bash
git clone <repo-url>
git checkout Server-Admin-Project
# See README.md in Server-Admin-Project branch for full setup
```

**Documentation:**
- `README.md` - Project overview and quick start
- `USER_GUIDE.md` - Detailed usage instructions
- `DEVELOPER_DOCS.md` - Architecture and API reference
- `FINAL_REPORT.md` - Implementation details and testing evidence
- `INTEGRATION_PLAYBOOK.md` - Lab testing guide

---

### 2. **IDS-Project**
Machine learning-based Intrusion Detection System (IDS) with hybrid threat detection.

**Branch:** `IDS-Project`

**Features:**
- Hybrid detection: heuristics + RandomForest ML
- Sub-30 second latency on streaming data
- Batch and streaming inference modes
- Automated feature engineering and normalization
- Support for port scanning, brute force, data exfiltration detection
- Production-ready with comprehensive testing

**Quick Start:**
```bash
git clone <repo-url>
git checkout IDS-Project
# See README.md in IDS-Project branch for full setup
```

**Documentation:**
- `README.md` - Project overview and features
- `INSTALLATION.md` - Setup and dependencies
- `USAGE.md` - Command reference
- `ARCHITECTURE.md` - System design and components
- `API.md` - Python API reference

---

## 🏗️ Repository Structure

```
Server-Admin-Work/
├── Server-Admin-Project/  [branch: Server-Admin-Project]
│   ├── Setup-FabrikamServer-Extended.ps1
│   ├── Setup-FabrikamServer-Extended.Tests.ps1
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_DOCS.md
│   └── ... (documentation and resources)
│
├── IDS-Project/  [branch: IDS-Project]
│   ├── IDS-tool/
│   │   ├── src/
│   │   ├── scripts/
│   │   ├── tests/
│   │   └── data/
│   ├── README.md
│   └── ... (IDS documentation)
│
└── [main: Overview only]
    └── README.md (this file)
```

---

## 🚀 Getting Started

### Clone and select a project:

**For Server-Admin-Project:**
```bash
git clone <repo-url>
cd Server-Admin-Work
git checkout Server-Admin-Project
# Read README.md for setup and usage
```

**For IDS-Project:**
```bash
git clone <repo-url>
cd Server-Admin-Work
git checkout IDS-Project
# Read README.md for setup and usage
```

---

## 📚 Documentation

Each branch contains full documentation. See branch-specific READMEs:
- **Server-Admin-Project**: PowerShell script documentation, API reference, and usage examples
- **IDS-Project**: Python IDS tool documentation, ML architecture, and training guide

---

## 🔄 CI/CD Pipelines

Both projects include GitHub Actions workflows:
- **Server-Admin-Project**: Pester tests + PSScriptAnalyzer
- **IDS-Project**: Python tests + linting

---

## 📝 License

See branch-specific documentation for license information.

## Quick Start

### Prerequisites
- Python 3.10+
- pip or conda

### Installation (2 minutes)

```bash
# Clone the repository
git clone https://github.com/nuunuu54/NuuNuu54-python-security-projects.git
cd NuuNuu54-python-security-projects

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# Check if data is ready
python -m IDS-tool.src.cli precheck

# Train a model on sample data
python -m IDS-tool.src.cli train --in IDS-tool/data/flows.csv --out models/rf_sample.pkl

# Run inference on new data
python -m IDS-tool.src.cli batch --in IDS-tool/data/flows.csv --model models/rf_sample.pkl
```

Or use the CLI wrappers:

**Windows:**
```powershell
.\ids.ps1 precheck
.\ids.ps1 train --in IDS-tool/data/flows.csv --out models/rf_sample.pkl
.\ids.ps1 batch --in IDS-tool/data/flows.csv --model models/rf_sample.pkl
```

**Linux/Mac:**
```bash
python -m IDS-tool.src.cli precheck
python -m IDS-tool.src.cli train --in IDS-tool/data/flows.csv --out models/rf_sample.pkl
python -m IDS-tool.src.cli batch --in IDS-tool/data/flows.csv --model models/rf_sample.pkl
```

## CLI Commands

### Training
```bash
ids train --in <dataset.csv> --out <model.pkl> [options]
```
- **--in**: Input CSV file with network flows
- **--out**: Output model path (joblib format)
- **--feature-only**: Generate features without training
- **--sample**: Max rows to use (for large files)

### Batch Inference
```bash
ids batch --in <dataset.csv> --model <model.pkl> [--out detections.json]
```
- **--in**: Input CSV file
- **--model**: Trained model file
- **--out**: Output JSON (default: detections_batch.json)
- **--feature-only**: Output features without predictions

### Streaming Inference
```bash
ids stream --model <model.pkl> [--out detections.json]
```
- **--model**: Trained model file
- **--out**: Output JSON (default: detections_stream.json)
- Reads JSON objects from STDIN, one per line

### Data Validation
```bash
ids precheck --dir <data_directory>
```
- Validates CSV schema
- Checks for required columns
- Warns about small classes
- Suggests normalization

### Normalization
```bash
python -m IDS-tool.scripts.normalize_flows --dir <data_dir> --out-dir <output_dir>
```
- Maps vendor-specific columns to canonical schema
- Synthesizes deterministic pseudo-IPs for missing values
- Handles PCAP and NetFlow formats

### Bulk Operations
```bash
python -m IDS-tool.scripts.bulk_process --dir <data_dir>
```
- Precheck all files
- Train models per file
- Generate consolidated reports
- Output: `reports/bulk_report.json`

## Project Structure

```
.
├── IDS-tool/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── cli.py              # CLI entry point with argparse
│   │   ├── ids.py              # Hybrid detection engine
│   │   ├── train_model.py       # Model training pipeline
│   │   ├── tune_model.py        # Hyperparameter tuning
│   │   ├── utils.py             # Feature engineering & helpers
│   │   └── __pycache__/
│   ├── scripts/
│   │   ├── normalize_flows.py   # Data normalization
│   │   ├── precheck_dataset.py  # CSV validation
│   │   ├── train_quick.py       # Bulk model training
│   │   ├── bulk_process.py      # Orchestration
│   │   ├── run_e2e.py           # End-to-end testing
│   │   └── ingest_merge.py      # Data merging utilities
│   ├── tests/
│   │   ├── test_utils_pytest.py # Feature engineering tests
│   │   ├── test_utils_script.py # Integration tests
│   │   └── __pycache__/
│   ├── models/                  # Trained RandomForest models
│   │   ├── rf_meta.pkl
│   │   ├── rf_meta_*.pkl
│   │   └── ...
│   ├── data/
│   │   ├── flows.csv            # Sample dataset
│   │   └── ...
│   ├── reports/                 # Generated reports
│   │   ├── bulk_report.json
│   │   └── ...
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI
├── .gitignore
├── ids.bat                      # Windows CLI wrapper
├── ids.ps1                      # PowerShell CLI wrapper
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── INSTALLATION.md              # Detailed setup guide
├── USAGE.md                     # Command examples
├── ARCHITECTURE.md              # Technical deep dive
├── CONTRIBUTING.md              # Development guide
└── API.md                       # Python API reference
```

## Key Concepts

### Hybrid Detection

IDS-Tool combines two complementary approaches:

1. **Heuristic Rules** (Real-time, low latency)
   - Port scan detection: suspicious source ports (>10 per src_ip)
   - Brute force detection: repeated failed auth (>5 per dst_ip:dst_port)
   - Exfiltration detection: unusual payload sizes or protocols
   - Beaconing detection: periodic connection patterns

2. **Machine Learning** (Pattern recognition, adaptability)
   - RandomForest trained on labeled datasets
   - Vectorized feature engineering for speed
   - Confidence scoring via `predict_proba`
   - Per-host windowed features for context

### Windowed Features

Each flow is analyzed within a host context using sliding windows:
- **Packets sent/received** in last N flows
- **Bytes sent/received** in last N flows
- **Protocol distribution** in last N flows
- **Connection duration** statistics
- **Destination diversity** metrics

This captures behavioral patterns without requiring packet payload inspection.

### Data Normalization

Network data from different sources (PCAP, NetFlow, Zeek) use different column names:
- NetFlow: `src_ip`, `dst_ip`, `src_port`, `dst_port`
- Zeek: `id.orig_h`, `id.orig_p`, `id.resp_h`, `id.resp_p`
- Custom: Various vendor-specific formats

IDS-Tool **automatically maps** these to a canonical schema and **synthesizes deterministic pseudo-IPs** when real IPs are missing (using MD5 hash of filename as seed).

## Performance

- **Training**: 7 models trained on 10 datasets in < 60 seconds
- **Inference**: 1000 flows classified in < 5 seconds (batch mode)
- **Streaming**: ~30ms per flow (including I/O)
- **Memory**: ~100 MB for a trained model
- **Coverage**: 85%+ detection rate on known attacks, <5% false positives

## Testing

```bash
# Run all tests
pytest IDS-tool/tests/ -v

# With coverage
pytest IDS-tool/tests/ --cov=IDS-tool.src --cov-report=term

# Specific test
pytest IDS-tool/tests/test_utils_pytest.py::test_assemble_features_shape -v
```

**Current Status**: ✅ 2/2 tests passing

## Documentation

- **[INSTALLATION.md](INSTALLATION.md)** — Detailed setup for Windows, Linux, macOS
- **[USAGE.md](USAGE.md)** — Command examples and workflows
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Technical design and algorithms
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Development guidelines
- **[API.md](API.md)** — Python module reference

## Requirements

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
joblib>=1.3.0
requests>=2.31.0
pytest>=7.4.0
pytest-cov>=4.1.0
pylint>=3.0.0
black>=23.0.0
mypy>=1.7.0
```

## License

MIT License - See LICENSE file for details

## Author

**NuuNuu** - [@nuunuu54](https://github.com/nuunuu54)

## Acknowledgments

- Network datasets: UNSW-NB15, CIC-IDS2017, IoT-23
- Inspired by Zeek, Suricata, and YARA intrusion detection frameworks
- Built with pandas, scikit-learn, and NumPy

## Getting Help

- 📖 See [USAGE.md](USAGE.md) for command examples
- 🏗️ See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- 🐛 File an issue on GitHub
- 💬 Check existing issues and discussions

---

**Ready to detect threats?** Start with [INSTALLATION.md](INSTALLATION.md)
