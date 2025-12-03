from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import load_flows, basic_features, windowed_host_features, assemble_features


def main():
    data_file = Path(__file__).resolve().parents[1] / 'data' / 'flows.csv'
    if not data_file.exists():
        print('data/flows.csv missing; please place a sample dataset there.')
        raise SystemExit(1)
    df = load_flows(data_file)
    print('Loaded rows:', len(df))
    basic_df, cats = basic_features(df)
    print('Basic features shape:', basic_df.shape, 'Categorical cols:', len(cats))
    win = windowed_host_features(df)
    print('Windowed features shape:', win.shape)
    X, cols = assemble_features(df)
    print('Assembled features shape:', X.shape)
    print('Sample feature columns:', cols[:10])
    print('All tests in test_utils_script completed successfully')


if __name__ == '__main__':
    main()
