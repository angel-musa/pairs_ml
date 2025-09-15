# models.py
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import RidgeCV, LogisticRegressionCV
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import BaseCrossValidator
import xgboost as xgb

class PurgedTimeSeriesSplit(BaseCrossValidator):
    def __init__(self, n_splits=5, embargo=5):
        self.n_splits, self.embargo = n_splits, embargo
    def split(self, X, y=None, groups=None):
        n = len(X); fold = n // (self.n_splits+1)
        for i in range(self.n_splits):
            tr_end = fold*(i+1); te_start = tr_end + self.embargo; te_end = fold*(i+2)
            if te_end <= te_start: continue
            yield np.arange(0,tr_end), np.arange(te_start, te_end)
    def get_n_splits(self, X=None, y=None, groups=None): return self.n_splits

def train_regressor(features: pd.DataFrame, use_xgb=False):
    clean = features.dropna()
    X = clean.drop(columns=["target"]); y = clean["target"]
    cv = PurgedTimeSeriesSplit(n_splits=5, embargo=5)

    if use_xgb:
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
            random_state=42, n_jobs=-1
        )
        preds = pd.Series(index=y.index, dtype=float)
        for tr, te in cv.split(X):
            mdl = model
            mdl.fit(X.iloc[tr], y.iloc[tr])
            preds.iloc[te] = mdl.predict(X.iloc[te])
        model.fit(X, y)
    else:
        model = Pipeline([("scaler", StandardScaler()), ("ridge", RidgeCV(alphas=np.logspace(-4,3,20), cv=cv))])
        preds = pd.Series(index=y.index, dtype=float)
        for tr, te in cv.split(X):
            mdl = model
            mdl.fit(X.iloc[tr], y.iloc[tr])
            preds.iloc[te] = mdl.predict(X.iloc[te])
        model.fit(X, y)

    valid = preds.notna()
    rmse_model = float(np.sqrt(mean_squared_error(y[valid], preds[valid])))
    rmse_naive = float(np.sqrt(mean_squared_error(y[valid], np.zeros_like(y[valid]))))
    return model, preds, rmse_model, rmse_naive

def train_meta_classifier(X_meta: pd.DataFrame, y_meta: pd.Series):
    """
    Simple, strong baseline: logistic regression with CV and scaling.
    Returns fitted pipeline and in-sample predicted probabilities aligned to X_meta.index.
    """
    if len(X_meta) < 100 or y_meta.nunique() < 2:
        return None, pd.Series(index=X_meta.index, dtype=float)
    cv = PurgedTimeSeriesSplit(n_splits=5, embargo=5)
    clf = Pipeline([
        ("scaler", StandardScaler()),
        ("logit", LogisticRegressionCV(Cs=10, cv=cv, max_iter=1000, class_weight="balanced"))
    ])
    # cross-validated predictions
    proba = pd.Series(index=X_meta.index, dtype=float)
    for tr, te in cv.split(X_meta):
        clf.fit(X_meta.iloc[tr], y_meta.iloc[tr])
        proba.iloc[te] = clf.predict_proba(X_meta.iloc[te])[:,1]
    # final fit
    clf.fit(X_meta, y_meta)
    return clf, proba
