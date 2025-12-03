import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import load_flows, assemble_features


def test_assemble_features_shape():
    df = load_flows(Path(__file__).resolve().parents[1] / 'data' / 'flows.csv')
    X, cols = assemble_features(df)
    assert X.shape[0] == len(df)
    assert len(cols) > 0
    assert not X.isna().any().any()


def test_load_flows_missing_columns_added():
    # create a small DataFrame with minimal columns missing and save temp
    import pandas as pd
    tmp = Path(__file__).resolve().parents[1] / 'data' / 'tmp_min.csv'
    pd.DataFrame([{'row_id':1,'src_ip':'1.1.1.1','dst_ip':'2.2.2.2'}]).to_csv(tmp, index=False)
    df2 = load_flows(tmp)
    assert 'bytes' in df2.columns
    tmp.unlink()
