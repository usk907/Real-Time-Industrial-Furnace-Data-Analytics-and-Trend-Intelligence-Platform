"""
Automated MySQL Database & Users Initializer for IEIP
Executes db/schema.sql and db/create_users.sql via PyMySQL.
Reads user credentials dynamically from generator/.env and server/.env.
"""
import os
import sys
import getpass
import re
from pathlib import Path

def load_env_file(filepath: Path) -> dict:
    vals = {}
    if filepath.exists():
        for line in filepath.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip("'\"")
    return vals

def extract_db_password_from_url(database_url: str) -> str:
    """Extracts password from a SQLAlchemy URL like mysql+pymysql://user:password@host:port/db."""
    match = re.search(r"://[^:]+:([^@]+)@", database_url)
    if match:
        return match.group(1)
    return ""

def main():
    try:
        import pymysql
    except ImportError:
        print("[ERROR] pymysql is not installed in this environment. Run using server/venv or generator/venv.")
        sys.exit(1)

    root_dir = Path(__file__).resolve().parent.parent
    schema_sql_path = root_dir / "db" / "schema.sql"
    users_sql_path = root_dir / "db" / "create_users.sql"
    gen_env_path = root_dir / "generator" / ".env"
    server_env_path = root_dir / "server" / ".env"

    if not schema_sql_path.exists() or not users_sql_path.exists():
        print("[ERROR] Could not locate db/schema.sql or db/create_users.sql")
        sys.exit(1)

    # Load credentials from .env files
    gen_env = load_env_file(gen_env_path)
    server_env = load_env_file(server_env_path)

    gen_password = gen_env.get("DB_PASSWORD", "")
    server_password = extract_db_password_from_url(server_env.get("DATABASE_URL", ""))
    admin_password = os.getenv("ADMIN_DB_PASSWORD", gen_password)

    # Determine default port (check env or default to 3307 / 3306)
    target_port = int(os.getenv("DB_PORT", gen_env.get("DB_PORT", "3307")))

    print("=" * 65)
    print("      IEIP MySQL Database & Users Initializer")
    print("=" * 65)
    print(f"Target MySQL: 127.0.0.1:{target_port}")
    print("-" * 65)

    if not gen_password:
        gen_password = getpass.getpass("Enter password for generator_user: ")
    if not server_password:
        server_password = getpass.getpass("Enter password for server_user: ")
    if not admin_password:
        admin_password = getpass.getpass("Enter password for admin_user (press Enter to reuse generator password): ") or gen_password

    # Prompt for root password
    if len(sys.argv) > 1:
        root_pwd = sys.argv[1]
    else:
        root_pwd = getpass.getpass("Enter MySQL 'root' password (press Enter if none): ")

    # Connect as root
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            port=target_port,
            user="root",
            password=root_pwd,
            autocommit=True
        )
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to MySQL as root on port {target_port}: {e}")
        print("Please check that your MySQL service is running and credentials are correct.")
        sys.exit(1)

    print(f"\n[1/3] Connected to MySQL successfully as root on port {target_port}.")

    def run_sql_content(content: str, label: str):
        print(f"Executing {label}...")
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
    run_sql_content(schema_sql_path.read_text(encoding="utf-8"), "schema.sql")

    # Run create_users.sql with password substitution
    print("\n[3/3] Creating users (generator_user, server_user, admin_user)...")
    users_sql = users_sql_path.read_text(encoding="utf-8")
    users_sql = users_sql.replace("{{GENERATOR_PASSWORD}}", gen_password)
    users_sql = users_sql.replace("{{SERVER_PASSWORD}}", server_password)
    users_sql = users_sql.replace("{{ADMIN_PASSWORD}}", admin_password)
    run_sql_content(users_sql, "create_users.sql")
    conn.close()

    # Verification: test generator_user connection
    print("\n" + "=" * 65)
    print("Verifying generator_user connection...")
    try:
        test_conn = pymysql.connect(
            host="127.0.0.1",
            port=target_port,
            user="generator_user",
            password=gen_password,
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
            port=target_port,
            user="server_user",
            password=server_password,
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
