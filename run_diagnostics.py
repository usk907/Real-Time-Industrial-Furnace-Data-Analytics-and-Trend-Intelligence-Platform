"""
System Diagnostics Runner (Legacy Shim)
Delegates to tests/diagnostics.py
"""
import sys
from tests.diagnostics import run_connectivity, run_tap_pipeline, run_all_pages

if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "--all"
    if arg in ["--conn", "--connectivity", "-c"]:
        run_connectivity()
    elif arg in ["--tap", "-t"]:
        run_tap_pipeline()
    elif arg in ["--pages", "-p"]:
        run_all_pages()
    else:
        run_connectivity()
        print("\n")
        run_tap_pipeline()
        print("\n")
        run_all_pages()
