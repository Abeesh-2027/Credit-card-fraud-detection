from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "fraud_model.joblib"

FEATURE_NAMES = [
    "amount",
    "hour",
    "distance_from_home_km",
    "distance_from_last_txn_km",
    "ratio_to_median_spend",
    "txns_last_24h",
    "is_foreign",
    "is_online",
    "is_new_merchant",
    "card_present",
]


def generate_dataset(n_samples: int = 20000, fraud_rate: float = 0.03, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic labeled transaction dataset."""
    rng = np.random.default_rng(seed)
    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    def legit_block(n):
        return pd.DataFrame({
            "amount": rng.gamma(shape=2.0, scale=35, size=n),
            "hour": rng.normal(loc=14, scale=4.5, size=n) % 24,
            "distance_from_home_km": np.abs(rng.normal(loc=5, scale=8, size=n)),
            "distance_from_last_txn_km": np.abs(rng.normal(loc=3, scale=6, size=n)),
            "ratio_to_median_spend": np.abs(rng.normal(loc=1.0, scale=0.4, size=n)),
            "txns_last_24h": rng.poisson(lam=1.5, size=n),
            "is_foreign": rng.binomial(1, 0.03, size=n),
            "is_online": rng.binomial(1, 0.35, size=n),
            "is_new_merchant": rng.binomial(1, 0.15, size=n),
            "card_present": rng.binomial(1, 0.6, size=n),
            "label": 0,
        })

    def fraud_block(n):
        return pd.DataFrame({
            "amount": rng.gamma(shape=2.2, scale=180, size=n),
            "hour": rng.choice(list(range(0, 6)) + list(range(22, 24)), size=n).astype(float)
                    + rng.normal(0, 1.0, size=n),
            "distance_from_home_km": np.abs(rng.normal(loc=450, scale=350, size=n)),
            "distance_from_last_txn_km": np.abs(rng.normal(loc=380, scale=300, size=n)),
            "ratio_to_median_spend": np.abs(rng.normal(loc=6.5, scale=3.0, size=n)),
            "txns_last_24h": rng.poisson(lam=6, size=n),
            "is_foreign": rng.binomial(1, 0.55, size=n),
            "is_online": rng.binomial(1, 0.8, size=n),
            "is_new_merchant": rng.binomial(1, 0.75, size=n),
            "card_present": rng.binomial(1, 0.1, size=n),
            "label": 1,
        })

    df = pd.concat([legit_block(n_legit), fraud_block(n_fraud)], ignore_index=True)
    df["hour"] = df["hour"] % 24
    df["amount"] = df["amount"].clip(lower=0.5)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def train_model() -> dict:
    df = generate_dataset()
    X = df[FEATURE_NAMES]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])
    pipeline.fit(X_train, y_train)

    probs = pipeline.predict_proba(X_test)[:, 1]
    preds = pipeline.predict(X_test)
    auc = roc_auc_score(y_test, probs)
    report = classification_report(y_test, preds, output_dict=True)

    joblib.dump(pipeline, MODEL_PATH)

    importances = dict(zip(FEATURE_NAMES, pipeline.named_steps["clf"].feature_importances_.tolist()))

    return {
        "auc": auc,
        "report": report,
        "feature_importances": importances,
    }


def load_model():
    if not MODEL_PATH.exists():
        train_model()
    return joblib.load(MODEL_PATH)


if __name__ == "__main__":
    metrics = train_model()
    print(f"Model trained. ROC-AUC: {metrics['auc']:.4f}")
    print("Feature importances:")
    for name, importance in sorted(metrics["feature_importances"].items(), key=lambda x: -x[1]):
        print(f"  {name:30s} {importance:.4f}")
