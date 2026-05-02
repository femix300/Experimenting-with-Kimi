"""
EdgeIQ Firebase Firestore Client
=================================
Safe initialization + thin wrapper around firebase-admin.

Place this file at: backend/utils/firebase_client.py

Design decisions:
- Uses module-level singleton pattern. The Firebase app initializes exactly
  once when Django starts (via apps.py ready() hook).
- All write operations go through this client so we can add logging,
  retries, and error handling in one place.
- Firestore DocumentReference IDs are deterministic (using market event_id
  or signal_id) so agents can update documents without querying first.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Safe Firebase App initialization (singleton via module import)
# ---------------------------------------------------------------------------
# Django's autoreloader imports modules twice on dev. We guard against
# AlreadyExistsError so the second import doesn't crash the process.

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from firebase_admin.exceptions import AlreadyExistsError
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. Firestore writes will be no-ops.")

# Module-level cache
_firebase_app = None
_db: "firestore.Client | None" = None


def _get_firebase_app():
    """Return the initialized Firebase app, or None if not configured."""
    global _firebase_app

    if not _FIREBASE_AVAILABLE:
        return None

    if _firebase_app is not None:
        return _firebase_app

    # Path to service account JSON. In production, mount via secrets manager.
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)

    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
    elif os.environ.get("FIREBASE_PROJECT_ID"):
        # GCP environments (App Engine, Cloud Run, GKE) have default credentials
        cred = credentials.ApplicationDefault()
    else:
        logger.error(
            "Firebase credentials not found. Set FIREBASE_CREDENTIALS_PATH "
            "in settings or FIREBASE_PROJECT_ID env var."
        )
        return None

    try:
        project_id = getattr(settings, "FIREBASE_PROJECT_ID", os.environ.get("FIREBASE_PROJECT_ID"))
        _firebase_app = firebase_admin.initialize_app(cred, {"projectId": project_id})
        logger.info(f"Firebase initialized for project: {project_id}")
    except AlreadyExistsError:
        # Autoreloader guard – get the existing app
        _firebase_app = firebase_admin.get_app()
        logger.debug("Firebase app already initialized (autoreloader guard).")
    except Exception as exc:
        logger.exception(f"Firebase initialization failed: {exc}")
        return None

    return _firebase_app


def get_firestore_client() -> "firestore.Client | None":
    """Return a Firestore client singleton. Safe to call from any thread."""
    global _db

    if _db is not None:
        return _db

    app = _get_firebase_app()
    if app is None:
        return None

    _db = firestore.client(app=app)
    return _db


# ---------------------------------------------------------------------------
# 2. Django AppConfig ready() hook
# ---------------------------------------------------------------------------
# Add the following to your existing apps.py files (or create a dedicated
# 'firestore' Django app). This ensures Firebase loads once at startup.
#
# Example for backend/config/apps.py or a new app:
#
#   class FirestoreConfig(AppConfig):
#       name = "utils"
#       verbose_name = "Firestore"
#
#       def ready(self):
#           from utils.firebase_client import get_firestore_client
#           get_firestore_client()
#
# Then in INSTALLED_APPS add: 'utils.apps.FirestoreConfig'
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 3. Collection name constants (sinle source of truth)
# ---------------------------------------------------------------------------
class Collection:
    MARKETS = "markets"
    PRICE_HISTORY = "price_history"
    QUANT_METRICS = "quant_metrics"
    AI_ANALYSES = "ai_analyses"
    SIGNALS = "signals"
    TRADES = "trades"
    USER_PROFILES = "user_profiles"
    PORTFOLIO_SNAPSHOTS = "portfolio_snapshots"
    AGENT_RUNS = "agent_runs"  # For tracking/monitoring agent executions
    BACKTEST_RESULTS = "backtest_results"


# ---------------------------------------------------------------------------
# 4. Serializer helpers (Firestore cannot store Decimal / datetime natively)
# ---------------------------------------------------------------------------

def firestore_serialize(obj: Any) -> Any:
    """
    Recursively convert Django/Python types to Firestore-serializable types.
    - Decimal   -> float
    - datetime  -> UTC datetime (Firestore native)
    - dict      -> recursive
    - list      -> recursive
    """
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        # Ensure UTC-aware
        if obj.tzinfo is None:
            return obj.replace(tzinfo=dt_timezone.utc)
        return obj.astimezone(dt_timezone.utc)
    if isinstance(obj, dict):
        return {k: firestore_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [firestore_serialize(i) for i in obj]
    return obj


def firestore_doc_to_dict(doc_snapshot) -> dict | None:
    """Convert a Firestore DocumentSnapshot to a plain dict with 'id' key."""
    if not doc_snapshot.exists:
        return None
    data = doc_snapshot.to_dict()
    data["id"] = doc_snapshot.id
    return data


# ---------------------------------------------------------------------------
# 5. Thin CRUD wrapper
# ---------------------------------------------------------------------------

class FirestoreClient:
    """
    Thin async-style wrapper over Firestore for EdgeIQ collections.

    All methods are synchronous (blocking) to keep the agent code simple.
    Firestore SDK handles connection pooling under the hood.
    """

    def __init__(self):
        self.db = get_firestore_client()
        if self.db is None:
            logger.warning("FirestoreClient initialized without valid DB connection.")

    # -- Health check -------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self.db is not None

    # -- Core helpers -------------------------------------------------------

    def collection(self, name: str):
        return self.db.collection(name)

    def doc(self, collection: str, doc_id: str):
        return self.db.collection(collection).document(doc_id)

    # -- Write operations ---------------------------------------------------

    def set(self, collection: str, doc_id: str, data: dict, merge: bool = False) -> bool:
        """
        Create or overwrite a document. Returns True on success.
        Use merge=True to perform an upsert (partial update).
        """
        if not self.db:
            return False
        try:
            payload = firestore_serialize(data)
            self.db.collection(collection).document(doc_id).set(payload, merge=merge)
            return True
        except Exception as exc:
            logger.exception(f"Firestore set error [{collection}/{doc_id}]: {exc}")
            return False

    def add(self, collection: str, data: dict) -> str | None:
        """
        Add a document with auto-generated ID. Returns the new doc ID.
        """
        if not self.db:
            return None
        try:
            payload = firestore_serialize(data)
            ref = self.db.collection(collection).add(payload)[1]
            return ref.id
        except Exception as exc:
            logger.exception(f"Firestore add error [{collection}]: {exc}")
            return None

    def update(self, collection: str, doc_id: str, data: dict) -> bool:
        """Partial update (only changes specified fields)."""
        if not self.db:
            return False
        try:
            payload = firestore_serialize(data)
            self.db.collection(collection).document(doc_id).update(payload)
            return True
        except Exception as exc:
            logger.exception(f"Firestore update error [{collection}/{doc_id}]: {exc}")
            return False

    def delete(self, collection: str, doc_id: str) -> bool:
        if not self.db:
            return False
        try:
            self.db.collection(collection).document(doc_id).delete()
            return True
        except Exception as exc:
            logger.exception(f"Firestore delete error [{collection}/{doc_id}]: {exc}")
            return False

    # -- Batch operations ---------------------------------------------------

    def batch_set(self, collection: str, docs: dict[str, dict], merge: bool = False) -> bool:
        """
        Write multiple documents in a single batch (atomic, max 500 ops).
        docs = {doc_id: data_dict, ...}
        """
        if not self.db:
            return False
        if not docs:
            return True
        try:
            batch = self.db.batch()
            col = self.db.collection(collection)
            for doc_id, data in docs.items():
                payload = firestore_serialize(data)
                batch.set(col.document(doc_id), payload, merge=merge)
            batch.commit()
            return True
        except Exception as exc:
            logger.exception(f"Firestore batch_set error [{collection}]: {exc}")
            return False

    # -- Read operations (for views / API compatibility) --------------------

    def get(self, collection: str, doc_id: str) -> dict | None:
        """Get a single document by ID."""
        if not self.db:
            return None
        try:
            doc = self.db.collection(collection).document(doc_id).get()
            return firestore_doc_to_dict(doc)
        except Exception as exc:
            logger.exception(f"Firestore get error [{collection}/{doc_id}]: {exc}")
            return None

    def query(
        self,
        collection: str,
        filters: list[tuple[str, str, Any]] | None = None,
        order_by: tuple[str, bool] | None = None,  # (field, descending)
        limit: int | None = None,
    ) -> list[dict]:
        """
        Simple query builder. Returns list of dicts.
        filters = [(field, op, value), ...]  e.g. [("is_active", "==", True)]
        """
        if not self.db:
            return []
        try:
            q = self.db.collection(collection)
            if filters:
                for field, op, value in filters:
                    q = q.where(field, op, value)
            if order_by:
                field, desc = order_by
                q = q.order_by(field, direction="DESCENDING" if desc else "ASCENDING")
            if limit:
                q = q.limit(limit)
            return [firestore_doc_to_dict(d) for d in q.stream() if d.exists]
        except Exception as exc:
            logger.exception(f"Firestore query error [{collection}]: {exc}")
            return []

    def collection_group_query(
        self,
        collection_id: str,
        filters: list[tuple[str, str, Any]] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Query across all subcollections with the given collection_id."""
        if not self.db:
            return []
        try:
            q = self.db.collection_group(collection_id)
            if filters:
                for field, op, value in filters:
                    q = q.where(field, op, value)
            if limit:
                q = q.limit(limit)
            return [firestore_doc_to_dict(d) for d in q.stream() if d.exists]
        except Exception as exc:
            logger.exception(f"Firestore collection_group error [{collection_id}]: {exc}")
            return []

    # -- Subcollection helpers ----------------------------------------------
    # Firestore best practice: nest time-series data under the parent doc
    # e.g. /markets/{market_id}/price_history/{timestamp_doc}

    def set_subdoc(
        self,
        parent_collection: str,
        parent_id: str,
        sub_collection: str,
        subdoc_id: str,
        data: dict,
        merge: bool = False,
    ) -> bool:
        if not self.db:
            return False
        try:
            payload = firestore_serialize(data)
            self.db.collection(parent_collection).document(parent_id) \
                .collection(sub_collection).document(subdoc_id) \
                .set(payload, merge=merge)
            return True
        except Exception as exc:
            logger.exception(f"Firestore subdoc error [{parent_collection}/{parent_id}/{sub_collection}/{subdoc_id}]: {exc}")
            return False

    def query_subcollection(
        self,
        parent_collection: str,
        parent_id: str,
        sub_collection: str,
        order_by: tuple[str, bool] | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        if not self.db:
            return []
        try:
            q = self.db.collection(parent_collection).document(parent_id) \
                .collection(sub_collection)
            if order_by:
                field, desc = order_by
                q = q.order_by(field, direction="DESCENDING" if desc else "ASCENDING")
            if limit:
                q = q.limit(limit)
            return [firestore_doc_to_dict(d) for d in q.stream() if d.exists]
        except Exception as exc:
            logger.exception(f"Firestore query_subcollection error: {exc}")
            return []


# ---------------------------------------------------------------------------
# 6. Singleton export
# ---------------------------------------------------------------------------
fs = FirestoreClient()
