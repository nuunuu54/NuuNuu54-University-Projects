# Contributing Guide

Contribute to IDS-Tool development!

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Adding Features](#adding-features)
- [Pull Request Process](#pull-request-process)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/NuuNuu54-python-security-projects.git`
3. Create feature branch: `git checkout -b feature/my-feature`
4. Make changes and commit: `git commit -m "Add my feature"`
5. Push to fork: `git push origin feature/my-feature`
6. Create Pull Request on GitHub

## Development Setup

```bash
# Clone repository
git clone https://github.com/nuunuu54/NuuNuu54-python-security-projects.git
cd NuuNuu54-python-security-projects

# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows

# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest IDS-tool/tests/ -v
```

## Code Standards

### Style (Black)

```bash
# Format code
black IDS-tool/src

# Check formatting
black IDS-tool/src --check
```

### Linting (Pylint)

```bash
# Run linter
pylint IDS-tool/src

# Target: score > 8.0
```

### Type Hints

```python
# Use type hints
def assemble_features(
    flows_df: pd.DataFrame, 
    window_size: int = 60
) -> Tuple[np.ndarray, List[str]]:
    """
    Generate features for all flows
    """
    pass
```

### Tests (Pytest)

```python
# Test new functions
def test_my_function():
    result = my_function(input_data)
    assert result == expected_output

# Run tests
pytest IDS-tool/tests/ -v
```

## Adding Features

### Add New Attack Detection

**File:** `IDS-tool/src/ids.py`

```python
def detect_my_attack(flows_by_src, threshold=10):
    """Detect custom attack pattern
    
    Args:
        flows_by_src: {src_ip: [flows]}
        threshold: Alert threshold
        
    Returns:
        (verdict, confidence)
    """
    results = []
    for src_ip, flows in flows_by_src.items():
        # Your detection logic
        if attack_detected:
            results.append({
                'src_ip': src_ip,
                'verdict': 'my_attack',
                'confidence': 0.85,
            })
    return results
```

### Add New CLI Command

**File:** `IDS-tool/src/cli.py`

```python
def cmd_my_command(args):
    """Handle 'ids my-command'"""
    print("Running my command...")
    # Implementation

# Register in main()
parser.add_subparsers(dest='command')
my_parser = parser.add_parser('my-command')
my_parser.add_argument('--option', required=True)
my_parser.set_defaults(func=cmd_my_command)
```

### Add New Feature

**File:** `IDS-tool/src/utils.py`

```python
def my_feature(flow: dict, window: List[dict]) -> float:
    """Compute custom feature
    
    Args:
        flow: Current flow
        window: Previous flows
        
    Returns:
        Feature value
    """
    pass

# Add to FEATURE_NAMES and assemble_features()
```

## Testing

### Run All Tests

```bash
pytest IDS-tool/tests/ -v
```

### Run Specific Test

```bash
pytest IDS-tool/tests/test_utils_pytest.py::test_name -v
```

### With Coverage

```bash
pytest IDS-tool/tests/ --cov=IDS-tool.src --cov-report=term
```

### Add Test

**File:** `IDS-tool/tests/test_my_feature.py`

```python
import pytest
from IDS-tool.src.my_module import my_function

def test_my_function():
    """Test my_function"""
    result = my_function(test_input)
    assert result == expected_output
    
def test_my_function_edge_case():
    """Test edge case"""
    result = my_function(edge_input)
    assert result is not None
```

## Pull Request Process

1. **Update Code** - Make changes in feature branch
2. **Run Tests** - Ensure all tests pass: `pytest IDS-tool/tests/ -v`
3. **Format Code** - Run black: `black IDS-tool/src`
4. **Lint Code** - Run pylint: `pylint IDS-tool/src`
5. **Write Tests** - Add tests for new features
6. **Update Docs** - Update README or API.md if needed
7. **Commit** - `git commit -m "Clear description of changes"`
8. **Push** - `git push origin feature/my-feature`
9. **Create PR** - On GitHub, fill in PR template
10. **Review** - Address review comments

## PR Template

```markdown
## Description
Brief description of changes

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update

## How to test
Steps to verify changes work

## Checklist
- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Linting passes (`pylint`)
- [ ] Documentation updated
```

## Commit Messages

```
# Good
git commit -m "Add port scan detection heuristic"
git commit -m "Fix windowed feature calculation for empty windows"

# Bad
git commit -m "fixes"
git commit -m "stuff"
```

## Documentation

### Update README.md
- Add feature overview
- Add usage examples

### Update USAGE.md
- Add command examples
- Show expected output

### Update ARCHITECTURE.md
- Explain technical design
- Include diagrams/code

### Add Docstrings
```python
def my_function(arg1: int, arg2: str) -> bool:
    """Short description
    
    Longer description explaining what this does
    
    Args:
        arg1: Description
        arg2: Description
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this happens
    """
    pass
```

## Reporting Issues

Use GitHub Issues with template:

```markdown
## Description
Clear description of issue

## Steps to reproduce
1. Step one
2. Step two

## Expected behavior
What should happen

## Actual behavior
What actually happens

## Environment
- Python version: 3.10+
- OS: Windows/Linux/Mac
```

## Code of Conduct

- Be respectful and inclusive
- Assume good intent
- Provide constructive feedback
- Help others learn

## Questions?

Open an issue or discussion on GitHub!

---

**Thank you for contributing!**
