"""
Root Pytest Configuration and Environment Fixtures for IEIP.
Configures python paths and test environment for both generator and server test suites.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
GENERATOR_DIR = REPO_ROOT / "generator"
SERVER_DIR = REPO_ROOT / "server"

for directory in (str(REPO_ROOT), str(GENERATOR_DIR), str(SERVER_DIR)):
    if directory not in sys.path:
        sys.path.insert(0, directory)

# Provide fallback test environment variables if server/.env is not present
server_env = SERVER_DIR / ".env"
if not server_env.exists():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("JWT_SECRET", "test_jwt_secret_key_minimum_32_characters_long")
    os.environ.setdefault("ADMIN_PASSWORD", "test_admin_secure_pass_123")
