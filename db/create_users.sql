-- Industrial Energy Intelligence Platform (IEIP)
-- Least-Privilege MySQL Users Setup (Localhost Only)

CREATE DATABASE IF NOT EXISTS furnace_db;
USE furnace_db;

-- 1. Generator User: INSERT/REPLACE on readings tables ONLY
CREATE USER IF NOT EXISTS 'generator_user'@'localhost' IDENTIFIED BY 'GenPassword123!';
CREATE USER IF NOT EXISTS 'generator_user'@'127.0.0.1' IDENTIFIED BY 'GenPassword123!';

-- Grant INSERT & DELETE/UPDATE (REPLACE is internally DELETE + INSERT) on furnace_readings & furnace_latest
GRANT INSERT ON furnace_db.furnace_readings TO 'generator_user'@'localhost';
GRANT INSERT ON furnace_db.furnace_readings TO 'generator_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE, DELETE ON furnace_db.furnace_latest TO 'generator_user'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON furnace_db.furnace_latest TO 'generator_user'@'127.0.0.1';

-- 2. Server User: SELECT on readings, SELECT/INSERT/UPDATE on users and alarms
CREATE USER IF NOT EXISTS 'server_user'@'localhost' IDENTIFIED BY 'ServerPassword123!';
CREATE USER IF NOT EXISTS 'server_user'@'127.0.0.1' IDENTIFIED BY 'ServerPassword123!';

GRANT SELECT ON furnace_db.furnace_readings TO 'server_user'@'localhost';
GRANT SELECT ON furnace_db.furnace_readings TO 'server_user'@'127.0.0.1';

GRANT SELECT ON furnace_db.furnace_latest TO 'server_user'@'localhost';
GRANT SELECT ON furnace_db.furnace_latest TO 'server_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE ON furnace_db.users TO 'server_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON furnace_db.users TO 'server_user'@'127.0.0.1';

GRANT SELECT, INSERT, UPDATE ON furnace_db.alarms TO 'server_user'@'localhost';
GRANT SELECT, INSERT, UPDATE ON furnace_db.alarms TO 'server_user'@'127.0.0.1';

-- 3. Admin / DDL Maintenance User: Full local management of furnace_db
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'AdminPassword123!';
CREATE USER IF NOT EXISTS 'admin_user'@'127.0.0.1' IDENTIFIED BY 'AdminPassword123!';

GRANT ALL PRIVILEGES ON furnace_db.* TO 'admin_user'@'localhost';
GRANT ALL PRIVILEGES ON furnace_db.* TO 'admin_user'@'127.0.0.1';

FLUSH PRIVILEGES;
