"""Small hyperparameter tuning harness using GridSearchCV.

This is intentionally small and meant for modest datasets. For large datasets use a dedicated tuning job.
"""
from pathlib import Path
import argparse
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from src.utils import load_flows, assemble_features


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--window', type=int, default=60)
    args = p.parse_args()

    df = load_flows(Path(args.input))
    label_col = None
    for name in ('label','class','attack','is_attack'):
        if name in df.columns:
            label_col = name
            break
    if label_col is None:
        raise SystemExit('No label column found')

    X, feature_cols = assemble_features(df, window_seconds=args.window)
    y = LabelEncoder().fit_transform(df[label_col].astype(str))

    p.add_argument('--random', action='store_true', help='Use RandomizedSearchCV instead of GridSearchCV')
    p.add_argument('--n-iter', type=int, default=10, help='Number of iterations for randomized search')
    p.add_argument('--out-cv', help='Optional path to save CV results CSV')
    pargs = p.parse_args()

    param_grid = {'n_estimators': [50,100,200], 'max_depth': [None, 10, 20, 30], 'max_features': ['sqrt','log2']}
    base = RandomForestClassifier(class_weight='balanced_subsample', random_state=42)
    if pargs.random:
        search = RandomizedSearchCV(base, param_grid, n_iter=pargs.n_iter, cv=3, n_jobs=1, verbose=1, random_state=42)
    else:
        search = GridSearchCV(base, param_grid, cv=3, n_jobs=1, verbose=1)

    search.fit(X, y)
    print('Best params:', search.best_params_)

    # Save CV results if requested
    if pargs.out_cv:
        try:
            res = pd.DataFrame(search.cv_results_)
            res.to_csv(pargs.out_cv, index=False)
            print('Saved CV results to', pargs.out_cv)
        except Exception:
            pass

    meta = {'model': search.best_estimator_, 'feature_columns': feature_cols, 'label_encoder': LabelEncoder().fit(df[label_col].astype(str)), 'window_seconds': args.window}
    joblib.dump(meta, args.out)
    print('Saved tuned model to', args.out)


if __name__ == '__main__':
    main()
