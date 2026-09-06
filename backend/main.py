from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from model import FEATURE_NAMES, load_model, train_model, MODEL_PATH
from auth import (
    LoginRequest,
    TokenResponse,
    create_access_token,
    require_auth,
    verify_credentials,
    ACCESS_TOKEN_MINUTES,
)

BASE_DIR = Path(__file__).parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

_model = None
_metrics_cache = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Train/load the model once at startup so the first request isn't slow.
    global _model
    _model = load_model()
    yield


app = FastAPI(title="Credit Card Fraud Detection API", version="1.0.0", lifespan=lifespan)

# ALLOWED_ORIGINS is a comma-separated list, e.g.
#   "https://your-app.vercel.app,http://localhost:5500"
# Set this in Render's environment variables once your Vercel URL exists.
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allow_origins = ["*"] if _origins_env.strip() == "*" else [o.strip() for o in _origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Transaction(BaseModel):
    amount: float = Field(..., ge=0, description="Transaction amount in your currency")
    hour: float = Field(..., ge=0, le=23.99, description="Hour of day the transaction occurred (0-23)")
    distance_from_home_km: float = Field(..., ge=0, description="Distance between cardholder's home and merchant")
    distance_from_last_txn_km: float = Field(..., ge=0, description="Distance from the previous transaction location")
    ratio_to_median_spend: float = Field(..., ge=0, description="Amount divided by the cardholder's median transaction amount")
    txns_last_24h: int = Field(..., ge=0, description="Number of transactions on this card in the last 24 hours")
    is_foreign: bool = Field(..., description="Whether the transaction is in a country different from the cardholder's home country")
    is_online: bool = Field(..., description="Whether this was a card-not-present online transaction")
    is_new_merchant: bool = Field(..., description="Whether the cardholder has never transacted with this merchant before")
    card_present: bool = Field(..., description="Whether the physical card was present (swiped/inserted/tapped)")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 842.50,
                "hour": 3,
                "distance_from_home_km": 620,
                "distance_from_last_txn_km": 580,
                "ratio_to_median_spend": 7.2,
                "txns_last_24h": 6,
                "is_foreign": True,
                "is_online": True,
                "is_new_merchant": True,
                "card_present": False,
            }
        }


class PredictionResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    top_signals: List[dict]


def _get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model


def _risk_level(prob: float) -> str:
    if prob < 0.2:
        return "low"
    if prob < 0.5:
        return "elevated"
    if prob < 0.8:
        return "high"
    return "critical"


def _explain(model, row: np.ndarray) -> List[dict]:
    """Rough per-transaction signal ranking using the forest's feature importances
    weighted by how far each feature is from a 'typical legit' baseline."""
    clf = model.named_steps["clf"]
    scaler = model.named_steps["scaler"]
    scaled = scaler.transform(row.reshape(1, -1))[0]
    importances = clf.feature_importances_
    contributions = np.abs(scaled) * importances
    order = np.argsort(-contributions)[:4]
    return [
        {"feature": FEATURE_NAMES[i], "influence": round(float(contributions[i]), 4)}
        for i in order
    ]


def _to_row(txn: Transaction) -> np.ndarray:
    return np.array([
        txn.amount,
        txn.hour,
        txn.distance_from_home_km,
        txn.distance_from_last_txn_km,
        txn.ratio_to_median_spend,
        txn.txns_last_24h,
        int(txn.is_foreign),
        int(txn.is_online),
        int(txn.is_new_merchant),
        int(txn.card_present),
    ], dtype=float)


@app.get("/api/health")
def health():
    return {"status": "ok", "model_trained": MODEL_PATH.exists()}


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    token = create_access_token(payload.username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=ACCESS_TOKEN_MINUTES,
        username=payload.username,
    )


@app.get("/api/auth/me")
def me(username: str = Depends(require_auth)):
    return {"username": username}


@app.get("/api/model-info")
def model_info(username: str = Depends(require_auth)):
    global _metrics_cache
    if _metrics_cache is None:
        # Retrain fresh to report metrics (cheap: ~1-2s on this dataset size)
        _metrics_cache = train_model()
        global _model
        _model = load_model()
    m = _metrics_cache
    return {
        "auc": round(m["auc"], 4),
        "precision_fraud": round(m["report"]["1"]["precision"], 4),
        "recall_fraud": round(m["report"]["1"]["recall"], 4),
        "f1_fraud": round(m["report"]["1"]["f1-score"], 4),
        "feature_importances": {k: round(v, 4) for k, v in m["feature_importances"].items()},
    }


@app.post("/api/predict", response_model=PredictionResponse)
def predict(txn: Transaction, username: str = Depends(require_auth)):
    try:
        model = _get_model()
        row = _to_row(txn)
        prob = float(model.predict_proba(row.reshape(1, -1))[0, 1])
        return PredictionResponse(
            fraud_probability=round(prob, 4),
            is_fraud=prob >= 0.5,
            risk_level=_risk_level(prob),
            top_signals=_explain(model, row),
        )
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/predict/batch")
def predict_batch(txns: List[Transaction], username: str = Depends(require_auth)):
    model = _get_model()
    results = []
    for txn in txns:
        row = _to_row(txn)
        prob = float(model.predict_proba(row.reshape(1, -1))[0, 1])
        results.append({
            "fraud_probability": round(prob, 4),
            "is_fraud": prob >= 0.5,
            "risk_level": _risk_level(prob),
        })
    return {"results": results}


# --- Serve frontend ---
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
