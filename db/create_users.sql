-- Industrial Energy Intelligence Platform (IEIP)
-- Least-Privilege MySQL Users Setup (Localhost Only)

CREATE DATABASE IF NOT EXISTS furnace_db;
USE furnace_db;

-- 1. Generator User: INSERT/REPLACE on readings tables ONLY
-- Replace {{GENERATOR_PASSWORD}} with your generator user password or run scripts/setup_mysql.py
CREATE USER IF NOT EXISTS 'generator_user'@'localhost' IDENTIFIED BY '{{GENERATOR_PASSWORD}}';
CREATE USER IF NOT EXISTS 'generator_user'@'127.0.0.1' IDENTIFIED BY '{{GENERATOR_PASSWORD}}';

-- Grant INSERT & DELETE/UPDATE (REPLACE is internally DELETE + INSERT) on furnace_readings & furnace_latest
GRANT INSERT ON furnace_db.furnace_readings TO 'generator_user'@'localhost';
GRANT INSERT ON furnace_db.furnace_readings TO 'generator_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE, DELETE ON furnace_db.furnace_latest TO 'generator_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON furnace_db.furnace_latest TO 'generator_user'@'127.0.0.1';

-- 2. Server User: SELECT on readings, SELECT/INSERT/UPDATE on users and alarms
-- Replace {{SERVER_PASSWORD}} with your server user password or run scripts/setup_mysql.py
CREATE USER IF NOT EXISTS 'server_user'@'localhost' IDENTIFIED BY '{{SERVER_PASSWORD}}';
CREATE USER IF NOT EXISTS 'server_user'@'127.0.0.1' IDENTIFIED BY '{{SERVER_PASSWORD}}';

GRANT SELECT ON furnace_db.furnace_readings TO 'server_user'@'localhost';
GRANT SELECT ON furnace_db.furnace_readings TO 'server_user'@'127.0.0.1';

GRANT SELECT ON furnace_db.furnace_latest TO 'server_user'@'localhost';
GRANT SELECT ON furnace_db.furnace_latest TO 'server_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE ON furnace_db.users TO 'server_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON furnace_db.users TO 'server_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE ON furnace_db.alarms TO 'server_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON furnace_db.alarms TO 'server_user'@'127.0.0.1';

-- 3. Admin / DDL Maintenance User: Full local management of furnace_db
-- Replace {{ADMIN_PASSWORD}} with your admin DB user password or run scripts/setup_mysql.py
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY '{{ADMIN_PASSWORD}}';
CREATE USER IF NOT EXISTS 'admin_user'@'127.0.0.1' IDENTIFIED BY '{{ADMIN_PASSWORD}}';

GRANT ALL PRIVILEGES ON furnace_db.* TO 'admin_user'@'localhost';
GRANT ALL PRIVILEGES ON furnace_db.* TO 'admin_user'@'127.0.0.1';

FLUSH PRIVILEGES;
