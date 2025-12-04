import argparse
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from src.utils import load_flows, assemble_features


def find_label_col(df: pd.DataFrame):
    for name in ("label", "class", "attack", "is_attack"):
        if name in df.columns:
            return name
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--window", type=int, default=60)
    p.add_argument(
        "--feature-only",
        action="store_true",
        help="Train using only per-flow features (disable windowed host features)",
    )
    args = p.parse_args()

    inp = Path(args.input)
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    df = load_flows(inp)
    label_col = find_label_col(df)
    if label_col is None:
        raise SystemExit(
            'No label column found in input. Add a "label" column with class names.'
        )

    # If user requested feature-only mode, set window to 0 to disable per-host window features
    win_seconds = 0 if args.feature_only else args.window
    X, feature_cols = assemble_features(df, window_seconds=win_seconds)
    y = df[label_col].astype(str)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # If any class has fewer than 2 samples, avoid stratified split (it will error).
    unique, counts = np.unique(y_enc, return_counts=True)
    if len(unique) == 1:
        # fallback: train on whole dataset but warn
        clf = RandomForestClassifier(
            n_estimators=50, class_weight="balanced_subsample", random_state=42
        )
        clf.fit(X, y_enc)
        print("Warning: single-class dataset; trained on full data")
    else:
        if counts.min() < 2:
            # small counts for some classes — do a random split without stratify
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_enc, test_size=0.25, random_state=42
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_enc, test_size=0.25, stratify=y_enc, random_state=42
            )

        clf = RandomForestClassifier(
            n_estimators=100, class_weight="balanced_subsample", random_state=42
        )
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        print(classification_report(y_test, preds, zero_division=0))

    meta = {
        "model": clf,
        "feature_columns": feature_cols,
        "label_encoder": le,
        "window_seconds": args.window,
    }
    joblib.dump(meta, outp)
    print("Saved model metadata to", outp)


if __name__ == "__main__":
    main()
