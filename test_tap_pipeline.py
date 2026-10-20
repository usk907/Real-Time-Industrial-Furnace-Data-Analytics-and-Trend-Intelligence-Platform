"""
TAP Pipeline Test (Legacy Shim)
Delegates to tests/test_tap_pipeline.py
"""
import sys
from tests.diagnostics import run_tap_pipeline

if __name__ == "__main__":
    success = run_tap_pipeline()
    sys.exit(0 if success else 1)
