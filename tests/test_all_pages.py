"""
IEIP Comprehensive Page API Test Suite
Uses tests.diagnostics and tests.helpers to benchmark all 12 page endpoints.
"""
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.diagnostics import run_all_pages

if __name__ == "__main__":
    run_all_pages()
