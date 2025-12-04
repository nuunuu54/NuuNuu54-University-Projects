# API Reference

Python module documentation for programmatic IDS-Tool usage.

## Table of Contents
- [Import Overview](#import-overview)
- [`ids.py` - Detection Engine](#idspy---detection-engine)
- [`train_model.py` - Training](#train_modelpy---training)
- [`utils.py` - Feature Engineering](#utilspy---feature-engineering)
- [Examples](#examples)

## Import Overview

```python
# Detection engine
from IDS-tool.src.ids import HybridDetector, detect_port_scan, detect_brute_force

# Training
from IDS-tool.src.train_model import train_model, predict_single

# Feature engineering
from IDS-tool.src.utils import assemble_features, assemble_single_flow_features

# Utilities
from IDS-tool.src.utils import load_csv_safe, get_label_column
```

## `ids.py` - Detection Engine

Main threat detection module with hybrid heuristics + ML.

### Class: `HybridDetector`

```python
from IDS-tool.src.ids import HybridDetector

class HybridDetector:
    """Hybrid detection engine combining heuristics and ML"""
    
    def __init__(self, model_path: str = None):
        """
        Initialize detector
        
        Args:
            model_path: Path to trained model pickle file
                       If None, use heuristics only
        """
        self.model_data = None
        if model_path:
            self.model_data = joblib.load(model_path)
    
    def detect_batch(self, flows: List[dict]) -> List[dict]:
        """
        Detect threats in batch of flows
        
        Args:
            flows: List of flow dicts with keys:
                   src_ip, dst_ip, src_port, dst_port, proto,
                   bytes, packets, duration, tcp_flags
        
        Returns:
            List of detections (dict) with keys:
            - src_ip, dst_ip, src_port, dst_port
            - heuristic_verdict, heuristic_score
            - ml_prediction, ml_confidence (if model provided)
            - combined_score, risk_level
        
        Example:
            >>> detector = HybridDetector('models/rf.pkl')
            >>> flows = [{'src_ip': '192.168.1.10', 'dst_ip': '10.0.0.1', ...}]
            >>> detections = detector.detect_batch(flows)
            >>> print(detections[0]['risk_level'])
            'HIGH'
        """
        pass
    
    def detect_stream(self, flow: dict) -> dict:
        """
        Detect threat in single flow
        
        Args:
            flow: Single flow dict
        
        Returns:
            Detection dict with scores and verdict
        
        Example:
            >>> flow = {'src_ip': '192.168.1.10', ...}
            >>> detection = detector.detect_stream(flow)
        """
        pass
```

### Function: `detect_port_scan`

```python
def detect_port_scan(src_ip: str, flows_by_src: dict, threshold: int = 10) -> Tuple[bool, float]:
    """
    Detect port scanning activity
    
    Args:
        src_ip: Source IP to analyze
        flows_by_src: {src_ip: [flows]} dictionary
        threshold: Alert if source connects to > N destinations
        
    Returns:
        (detected: bool, confidence: float)
    
    Example:
        >>> flows_by_src = {'192.168.1.10': [flow1, flow2, ...]}
        >>> detected, conf = detect_port_scan('192.168.1.10', flows_by_src)
        >>> print(f"Port scan: {detected}, confidence: {conf:.2f}")
        Port scan: True, confidence: 0.92
    """
    pass
```

### Function: `detect_brute_force`

```python
def detect_brute_force(dst_ip: str, dst_port: int, flows_by_dst: dict, threshold: int = 5) -> Tuple[bool, float]:
    """
    Detect brute force attack
    
    Args:
        dst_ip: Destination IP
        dst_port: Destination port
        flows_by_dst: {(dst_ip, dst_port): [flows]} dictionary
        threshold: Alert if > N sources attack same destination:port
        
    Returns:
        (detected: bool, confidence: float)
    
    Example:
        >>> flows_by_dst = {('10.0.0.1', 22): [flow1, flow2, ...]}
        >>> detected, conf = detect_brute_force('10.0.0.1', 22, flows_by_dst)
    """
    pass
```

### Function: `detect_exfiltration`

```python
def detect_exfiltration(flow: dict, host_stats: dict) -> Tuple[bool, float]:
    """
    Detect data exfiltration
    
    Args:
        flow: Flow dictionary
        host_stats: Statistics for source IP
        
    Returns:
        (detected: bool, confidence: float)
    """
    pass
```

### Function: `detect_beaconing`

```python
def detect_beaconing(src_ip: str, flows_by_src: dict, time_window: int = 60) -> Tuple[bool, float]:
    """
    Detect periodic beaconing activity
    
    Args:
        src_ip: Source IP to analyze
        flows_by_src: {src_ip: [flows]} dictionary
        time_window: Check for periodicity in seconds
        
    Returns:
        (detected: bool, confidence: float)
    """
    pass
```

## `train_model.py` - Training

Model training and inference module.

### Function: `train_model`

```python
def train_model(
    csv_file: str,
    output_model: str,
    window_size: int = 60,
    sample_rows: int = None,
    feature_only: bool = False
) -> dict:
    """
    Train RandomForest model on labeled flows
    
    Args:
        csv_file: Input CSV with flows and labels
        output_model: Output model.pkl path
        window_size: Windowed features window size
        sample_rows: Max rows to use (for fast iteration)
        feature_only: If True, skip training (features only)
        
    Returns:
        {
            'status': 'success' or 'error',
            'model_path': path to saved model,
            'accuracy': training accuracy,
            'n_samples': number of flows,
            'n_classes': number of classes,
            'feature_names': list of features used
        }
    
    Example:
        >>> result = train_model('data/flows.csv', 'models/rf.pkl')
        >>> print(f"Accuracy: {result['accuracy']:.2%}")
        Accuracy: 92%
    """
    pass
```

### Function: `predict_single`

```python
def predict_single(
    flow: dict,
    model_path: str,
    flows_window: List[dict] = None
) -> dict:
    """
    Predict label for single flow
    
    Args:
        flow: Flow dictionary
        model_path: Path to trained model.pkl
        flows_window: Previous flows for windowed features
        
    Returns:
        {
            'prediction': predicted label (str),
            'confidence': prediction confidence (float),
            'probabilities': class probabilities (dict)
        }
    
    Example:
        >>> flow = {'src_ip': '192.168.1.10', ...}
        >>> result = predict_single(flow, 'models/rf.pkl')
        >>> print(result['prediction'])
        'port_scan'
    """
    pass
```

## `utils.py` - Feature Engineering

Feature extraction and data utilities.

### Function: `assemble_features`

```python
def assemble_features(
    flows_df: pd.DataFrame,
    window_size: int = 60
) -> Tuple[np.ndarray, List[str]]:
    """
    Generate feature matrix for all flows
    
    Args:
        flows_df: DataFrame with columns:
                  src_ip, dst_ip, src_port, dst_port, proto,
                  bytes, packets, duration, tcp_flags
        window_size: Windowed context size (flows)
        
    Returns:
        (features_array: np.ndarray shape (N, 20),
         feature_names: list of feature names)
    
    Features Generated (20 total):
        - Raw: src_port, dst_port, proto, bytes, packets, duration (6)
        - Windowed: bytes_sum, packets_sum, unique_dst_ips,
                    unique_ports, bytes_per_packet, avg_duration,
                    duration_std, bytes_zscore, packets_zscore (14)
    
    Example:
        >>> df = pd.read_csv('flows.csv')
        >>> X, names = assemble_features(df, window_size=60)
        >>> print(X.shape)
        (1000, 20)
        >>> print(names)
        ['src_port', 'dst_port', ...]
    """
    pass
```

### Function: `assemble_single_flow_features`

```python
def assemble_single_flow_features(
    flow: dict,
    flows_window: List[dict],
    feature_names: List[str] = None
) -> np.ndarray:
    """
    Generate features for single flow with windowed context
    
    Args:
        flow: Single flow dictionary
        flows_window: Previous flows (for windowed features)
        feature_names: Expected feature order
        
    Returns:
        Feature vector np.ndarray shape (20,)
    
    Example:
        >>> flow = {'src_ip': '192.168.1.10', 'dst_port': 80, ...}
        >>> window = [previous_flow1, previous_flow2, ...]
        >>> features = assemble_single_flow_features(flow, window)
        >>> print(features.shape)
        (20,)
    """
    pass
```

### Function: `load_csv_safe`

```python
def load_csv_safe(csv_file: str) -> pd.DataFrame:
    """
    Load CSV with error handling and validation
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        DataFrame with required columns
        
    Raises:
        ValueError: If required columns missing
        
    Example:
        >>> df = load_csv_safe('flows.csv')
    """
    pass
```

### Function: `get_label_column`

```python
def get_label_column(df: pd.DataFrame) -> Tuple[str, int]:
    """
    Detect label column in DataFrame
    
    Looks for: 'label', 'class', 'attack', 'is_attack'
    
    Args:
        df: DataFrame
        
    Returns:
        (column_name: str, n_classes: int)
        
    Raises:
        ValueError: If no label column found
        
    Example:
        >>> df = pd.read_csv('flows.csv')
        >>> label_col, n_classes = get_label_column(df)
        >>> print(f"Label column: {label_col}, classes: {n_classes}")
        Label column: attack, classes: 5
    """
    pass
```

## Examples

### Example 1: Train and Predict

```python
from IDS_tool.src.train_model import train_model, predict_single
import json

# Train model
result = train_model('data/flows.csv', 'models/rf.pkl')
print(f"Model trained: {result['accuracy']:.2%} accuracy")

# Make predictions
flow = {
    'src_ip': '192.168.1.10',
    'dst_ip': '10.0.0.1',
    'src_port': 54321,
    'dst_port': 80,
    'proto': 'TCP',
    'bytes': 5120,
    'packets': 52,
    'duration': 10.5,
    'tcp_flags': 'SYN'
}

pred = predict_single(flow, 'models/rf.pkl')
print(json.dumps(pred, indent=2))
```

### Example 2: Batch Detection

```python
from IDS_tool.src.ids import HybridDetector
import pandas as pd

# Load flows
df = pd.read_csv('data/flows.csv')
flows = df.to_dict('records')

# Detect threats
detector = HybridDetector('models/rf.pkl')
detections = detector.detect_batch(flows)

# Filter high-risk
high_risk = [d for d in detections if d['risk_level'] == 'HIGH']
print(f"Found {len(high_risk)} high-risk flows")

# Export results
import json
with open('detections.json', 'w') as f:
    json.dump(detections, f, indent=2)
```

### Example 3: Feature Inspection

```python
from IDS_tool.src.utils import assemble_features
import pandas as pd

# Load data
df = pd.read_csv('data/flows.csv')

# Generate features
X, feature_names = assemble_features(df, window_size=60)

# Analyze features
print(f"Shape: {X.shape}")
print(f"Features: {feature_names}")

# Export for analysis
feature_df = pd.DataFrame(X, columns=feature_names)
feature_df.to_csv('features.csv', index=False)
```

### Example 4: Custom Heuristic Integration

```python
from IDS_tool.src.ids import HybridDetector, detect_port_scan

class CustomDetector(HybridDetector):
    """Extend detector with custom rules"""
    
    def detect_custom_attack(self, flows_by_src):
        """Custom detection logic"""
        results = []
        for src_ip, flows in flows_by_src.items():
            if self._is_suspicious(flows):
                results.append({
                    'src_ip': src_ip,
                    'verdict': 'custom_attack',
                    'confidence': 0.8
                })
        return results
    
    def _is_suspicious(self, flows):
        """Check custom condition"""
        # Your logic here
        pass

# Use custom detector
detector = CustomDetector('models/rf.pkl')
detections = detector.detect_batch(flows)
```

---

**More Examples**: See [USAGE.md](USAGE.md) for CLI examples.
