"""
IEIP TAP Server & SQL Pipeline Verification
Delegates to unified diagnostics suite (run_diagnostics.py)
"""
from run_diagnostics import run_tap_pipeline

if __name__ == "__main__":
    run_tap_pipeline()
