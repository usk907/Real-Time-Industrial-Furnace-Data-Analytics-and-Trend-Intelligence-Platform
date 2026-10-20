"""
CLI SQL Query Tool (Delegates to view_db unified engine)
Preserves backwards compatibility for scripts executing query_db.py
"""
import sys
from view_db import execute_query

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_db.py \"YOUR SQL QUERY\"")
        print("Example: python query_db.py \"SHOW TABLES;\"")
        sys.exit(0)
    execute_query(" ".join(sys.argv[1:]))
