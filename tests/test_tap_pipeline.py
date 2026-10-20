"""
IEIP TAP Server & SQL Pipeline Verification Test
Uses tests.diagnostics and tests.helpers to verify ingestion pipeline.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.diagnostics import run_tap_pipeline

if __name__ == "__main__":
    success = run_tap_pipeline()
    sys.exit(0 if success else 1)
