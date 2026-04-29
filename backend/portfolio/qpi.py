"""
QPI (Quant Performance Index) Scoring System.
Weighted composite score: win_rate * 0.4 + ev_accuracy * 0.3 + kelly_compliance * 0.3
"""
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


@dataclass
class QPIResult:
    """QPI calculation result."""
    score: float  # 0-100
    win_rate_weight: float
    ev_accuracy_weight: float
    kelly_compliance_weight: float
    trend: str  # 'up', 'down', 'stable'
    version: int
    calculated_at: str
    components: Dict[str, float]


class QPIService:
    """Calculate and version QPI scores for users."""

    WEIGHTS = {
        "win_rate": 0.40,
        "ev_accuracy": 0.30,
        "kelly_compliance": 0.30,
    }

    def __init__(self, firebase_client):
        self.db = firebase_client.db

    def calculate(self, user_id: str, trades: Optional[List[Dict]] = None) -> QPIResult:
        """Calculate QPI score for a user."""
        # Fetch trades if not provided
        if trades is None:
            trades = self._fetch_trades(user_id)

        if not trades:
            return QPIResult(
                score=0.0,
                win_rate_weight=self.WEIGHTS["win_rate"],
                ev_accuracy_weight=self.WEIGHTS["ev_accuracy"],
                kelly_compliance_weight=self.WEIGHTS["kelly_compliance"],
                trend="stable",
                version=1,
                calculated_at=datetime.utcnow().isoformat(),
                components={"win_rate": 0, "ev_accuracy": 0, "kelly_compliance": 0},
            )

        # Component 1: Win Rate (0-100)
        closed = [t for t in trades if t.get("status") in ("won", "lost")]
        total_closed = len(closed)
        wins = len([t for t in closed if t.get("status") == "won"])
        win_rate = (wins / total_closed * 100) if total_closed > 0 else 0

        # Component 2: EV Accuracy (0-100)
        # Compare predicted EV to actual outcomes
        ev_trades = [t for t in closed if t.get("recommended_stake") and t.get("pnl") is not None]
        if ev_trades:
            predicted_pnl = sum(t["recommended_stake"] * 0.1 for t in ev_trades)  # simplified
            actual_pnl = sum(t["pnl"] for t in ev_trades)
            ev_accuracy = min(100, max(0, 50 + (actual_pnl / max(abs(predicted_pnl), 0.01)) * 50))
        else:
            ev_accuracy = 50  # neutral

        # Component 3: Kelly Compliance (0-100)
        kelly_compliant = len([t for t in trades if t.get("kelly_compliant", False)])
        total_with_kelly = len([t for t in trades if "kelly_compliant" in t])
        kelly_compliance = (kelly_compliant / total_with_kelly * 100) if total_with_kelly > 0 else 0

        # Calculate weighted score
        score = (
            win_rate * self.WEIGHTS["win_rate"] +
            ev_accuracy * self.WEIGHTS["ev_accuracy"] +
            kelly_compliance * self.WEIGHTS["kelly_compliance"]
        )

        # Determine trend by comparing with previous score
        previous = self._get_previous_qpi(user_id)
        trend = "stable"
        if previous:
            diff = score - previous["score"]
            if diff > 2:
                trend = "up"
            elif diff < -2:
                trend = "down"

        # Versioning
        version = (previous.get("version", 0) + 1) if previous else 1

        result = QPIResult(
            score=round(min(100, max(0, score)), 1),
            win_rate_weight=self.WEIGHTS["win_rate"],
            ev_accuracy_weight=self.WEIGHTS["ev_accuracy"],
            kelly_compliance_weight=self.WEIGHTS["kelly_compliance"],
            trend=trend,
            version=version,
            calculated_at=datetime.utcnow().isoformat(),
            components={
                "win_rate": round(win_rate, 1),
                "ev_accuracy": round(ev_accuracy, 1),
                "kelly_compliance": round(kelly_compliance, 1),
            },
        )

        # Store result
        self._store_qpi(user_id, result)

        return result

    def _fetch_trades(self, user_id: str) -> List[Dict]:
        """Fetch trades for user from Firestore."""
        try:
            docs = self.db.collection("trades").where("user_id", "==", user_id).stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception:
            return []

    def _get_previous_qpi(self, user_id: str) -> Optional[Dict]:
        """Get the most recent QPI calculation for a user."""
        try:
            docs = (
                self.db.collection("qpi_scores")
                .where("user_id", "==", user_id)
                .order_by("version", direction="DESCENDING")
                .limit(1)
                .stream()
            )
            for doc in docs:
                return doc.to_dict()
            return None
        except Exception:
            return None

    def _store_qpi(self, user_id: str, result: QPIResult):
        """Store QPI calculation result."""
        doc_id = hashlib.md5(f"{user_id}_{result.version}".encode()).hexdigest()
        self.db.collection("qpi_scores").document(doc_id).set({
            "user_id": user_id,
            "score": result.score,
            "components": result.components,
            "trend": result.trend,
            "version": result.version,
            "calculated_at": result.calculated_at,
        })
