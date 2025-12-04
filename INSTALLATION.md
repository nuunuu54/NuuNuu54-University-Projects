# Installation Guide

## Table of Contents
- [System Requirements](#system-requirements)
- [Windows Setup](#windows-setup)
- [Linux/Mac Setup](#linuxmac-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

- **Python**: 3.10 or later
- **RAM**: 2 GB minimum (4 GB recommended for training large datasets)
- **Disk**: 500 MB free space (including models and data)
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)

## Windows Setup

### Step 1: Clone the Repository

```powershell
# Choose a directory (e.g., C:\projects or C:\Users\YourName\Desktop)
cd C:\Users\YourName\Desktop

git clone https://github.com/nuunuu54/NuuNuu54-python-security-projects.git
cd NuuNuu54-python-security-projects
```

### Step 2: Create Virtual Environment

```powershell
# Create venv in project root
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation

```powershell
# Test Python import
python -c "import pandas, numpy, sklearn; print('All packages imported successfully')"

# Run tests
pytest IDS-tool/tests/ -v

# Test CLI
.\ids.ps1 precheck
```

## Linux/Mac Setup

### Step 1: Clone the Repository

```bash
# Choose a directory
cd ~/projects  # or any preferred location
git clone https://github.com/nuunuu54/NuuNuu54-python-security-projects.git
cd NuuNuu54-python-security-projects
```

### Step 2: Create Virtual Environment

```bash
# Create venv in project root
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Test Python import
python -c "import pandas, numpy, sklearn; print('All packages imported successfully')"

# Run tests
pytest IDS-tool/tests/ -v

# Test CLI
python -m IDS-tool.src.cli precheck
```

## Verification

Run the following commands to verify everything is working:

```powershell
# 1. Check venv activation
.\.venv\Scripts\python.exe --version

# 2. Run precheck (validates CSV schema on sample data)
.\ids.ps1 precheck

# 3. Quick model training (should complete in < 5 seconds)
.\ids.ps1 train --in IDS-tool/data/flows.csv --out models/test_rf.pkl

# 4. Run batch inference
.\ids.ps1 batch --in IDS-tool/data/flows.csv --model models/test_rf.pkl

# 5. Run tests
pytest IDS-tool/tests/ -v --tb=short
```

**Expected Output:**
```
All packages imported successfully
Precheck passed: IDS-tool/data/flows.csv
Training complete: 2 classes, 100 samples
Batch inference: 100 detections
2 passed in 0.37s
```

## Troubleshooting

### Issue: "python: command not found"

**Solution**: Python may not be in PATH. Use full path or reinstall Python with "Add Python to PATH" checked.

```powershell
# Find Python installation
Get-Command python  # If this fails, Python isn't in PATH
# Reinstall Python from python.org with "Add to PATH" option
```

### Issue: "pip install" fails with "Permission denied"

**Solution**: Use `--user` flag or ensure venv is activated.

```powershell
# Ensure venv is activated
.\.venv\Scripts\Activate.ps1

# Then retry pip install
pip install -r requirements.txt
```

### Issue: "ModuleNotFoundError: No module named 'IDS_tool'"

**Solution**: Ensure you're using the project's venv Python.

```powershell
# Use full path to venv Python
.\.venv\Scripts\python.exe -m IDS-tool.src.cli precheck

# Or activate venv and use `python` command
.\.venv\Scripts\Activate.ps1
python -m IDS-tool.src.cli precheck
```

### Issue: "No such file or directory: IDS-tool/data/flows.csv"

**Solution**: Ensure you're in the project root directory.

```powershell
# Check current directory
pwd  # Should show path ending in /NuuNuu54-python-security-projects

# Verify file exists
Test-Path IDS-tool/data/flows.csv  # Should return True

# If not, navigate to project root
cd ..
cd NuuNuu54-python-security-projects
```

### Issue: Tests fail with "ImportError"

**Solution**: Run tests from project root with venv activated.

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Ensure in project root
pwd

# Run tests
pytest IDS-tool/tests/ -v
```

### Issue: "The system cannot find the file specified" on Windows

**Solution**: Ensure PowerShell is set to allow script execution.

```powershell
# Check policy
Get-ExecutionPolicy

# If "Restricted", allow RemoteSigned scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Re-run CLI
.\ids.ps1 precheck
```

## Next Steps

Once installation is verified:

1. Read [USAGE.md](USAGE.md) for CLI command examples
2. Read [QUICK_START.md](QUICK_START.md) for first model training
3. Check [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
4. Review [API.md](API.md) for Python integration

## Getting Help

- Check [USAGE.md](USAGE.md) for command reference
- Run `python -m IDS-tool.src.cli --help` for CLI help
- Review test files: `IDS-tool/tests/test_utils_pytest.py`
- Open an issue on GitHub
