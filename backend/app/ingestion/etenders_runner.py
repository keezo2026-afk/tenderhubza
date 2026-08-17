"""Backward-compatible import for the Phase 1 eTender runner.

All source-independent behavior now lives in :mod:`app.ingestion.engine`.
"""

from app.ingestion.engine import IngestionEngine

ETendersIngestionService = IngestionEngine

__all__ = ["ETendersIngestionService", "IngestionEngine"]
