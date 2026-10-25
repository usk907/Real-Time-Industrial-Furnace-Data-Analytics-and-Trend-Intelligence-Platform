"""
Automated MySQL Database & Users Initializer for IEIP
Executes db/schema.sql and db/create_users.sql via PyMySQL.
"""
import sys
import getpass
from pathlib import Path

def main():
    try:
        import pymysql
    except ImportError:
        print("[ERROR] pymysql is not installed in this environment. Run using server/venv or generator/venv.")
        sys.exit(1)

    root_dir = Path(__file__).resolve().parent.parent
    schema_sql_path = root_dir / "db" / "schema.sql"
    users_sql_path = root_dir / "db" / "create_users.sql"

    if not schema_sql_path.exists() or not users_sql_path.exists():
        print("[ERROR] Could not locate db/schema.sql or db/create_users.sql")
        sys.exit(1)

    print("=" * 65)
    print("      IEIP MySQL Database & Users Initializer")
    print("=" * 65)
    print("This utility will connect to local MySQL (127.0.0.1:3306) as 'root',")
    print("create the 'furnace_db' database, tables, and least-privilege users.")
    print("-" * 65)

    # Prompt for root password
    if len(sys.argv) > 1:
        root_pwd = sys.argv[1]
    else:
        root_pwd = getpass.getpass("Enter MySQL 'root' password (press Enter if none): ")

    # Connect as root
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password=root_pwd,
            autocommit=True
        )
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to MySQL as root: {e}")
        print("Please check that your MySQL service is running on 127.0.0.1:3306 and password is correct.")
        sys.exit(1)

    print("\n[1/3] Connected to MySQL successfully as root.")

    def run_sql_file(filepath):
        print(f"Executing {filepath.name}...")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split on semicolons, ignoring comments
        statements = []
        current = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("--") or not stripped:
                continue
            current.append(line)
            if stripped.endswith(";"):
                stmt = "\n".join(current)
                if stmt.strip().rstrip(";"):
                    statements.append(stmt.strip())
                current = []

        with conn.cursor() as cursor:
            for stmt in statements:
                try:
                    cursor.execute(stmt)
                except Exception as err:
                    print(f"  [WARN on statement]: {err}")

    # Run schema.sql
    print("\n[2/3] Creating database schema & tables...")
    run_sql_file(schema_sql_path)

    # Run create_users.sql
    print("\n[3/3] Creating users (generator_user, server_user, admin_user)...")
    run_sql_file(users_sql_path)
    conn.close()

    # Verification: test generator_user connection
    print("\n" + "=" * 65)
    print("Verifying generator_user connection...")
    try:
        test_conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="generator_user",
            password="GenPassword123!",
            database="furnace_db"
        )
        test_conn.close()
        print(" [OK] generator_user connected to furnace_db successfully!")
    except Exception as e:
        print(f" [FAIL] generator_user verification failed: {e}")

    # Verification: test server_user connection
    print("Verifying server_user connection...")
    try:
        test_conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="server_user",
            password="ServerPassword123!",
            database="furnace_db"
        )
        test_conn.close()
        print(" [OK] server_user connected to furnace_db successfully!")
    except Exception as e:
        print(f" [FAIL] server_user verification failed: {e}")

    print("=" * 65)
    print(" DATABASE SETUP COMPLETE! You can now start the generator and server.")
    print("=" * 65)

if __name__ == "__main__":
    main()
