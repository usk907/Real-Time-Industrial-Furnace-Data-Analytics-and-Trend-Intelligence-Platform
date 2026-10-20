"""
Database Inspector & Query Tool (Legacy Shim)
Delegates to scripts/tools/db_tool.py
"""
import os
import sys

_tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "tools"))
if _tools_path not in sys.path:
    sys.path.insert(0, _tools_path)

from db_tool import inspect_db, execute_query

if __name__ == "__main__":
    if len(sys.argv) > 1:
        raw_arg = " ".join(sys.argv[1:])
        if raw_arg.startswith("--query="):
            execute_query(raw_arg.split("=", 1)[1])
        elif raw_arg == "--inspect":
            inspect_db()
        else:
            execute_query(raw_arg)
    else:
        inspect_db()
