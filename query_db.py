"""
CLI SQL Query Tool (Legacy Shim)
Delegates to scripts/tools/db_tool.py
"""
import os
import sys

_tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "scripts", "tools"))
if _tools_path not in sys.path:
    sys.path.insert(0, _tools_path)

from db_tool import execute_query

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_db.py \"YOUR SQL QUERY\"")
        print("Example: python query_db.py \"SHOW TABLES;\"")
        sys.exit(0)
    execute_query(" ".join(sys.argv[1:]))
