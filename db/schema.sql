-- Industrial Energy Intelligence Platform (IEIP)
-- Core Database Schema (Contract 1 <-> 2)

CREATE DATABASE IF NOT EXISTS furnace_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE furnace_db;

-- 1. Continuous Time-Series Telemetry Table
CREATE TABLE IF NOT EXISTS furnace_readings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME(3) NOT NULL,
    tag VARCHAR(64) NOT NULL,
    value DOUBLE NOT NULL,
    quality TINYINT DEFAULT 1,
    INDEX idx_ts (ts),
    INDEX idx_tag_ts (tag, ts)
) ENGINE=InnoDB;

-- 2. Latest Value Cache for Rapid Live Monitoring and WebSocket Broadcast
CREATE TABLE IF NOT EXISTS furnace_latest (
    tag VARCHAR(64) PRIMARY KEY,
    value DOUBLE NOT NULL,
    ts DATETIME(3) NOT NULL
) ENGINE=InnoDB;

-- 3. User Authentication and Role-Based Access Control (RBAC)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'engineer', 'operator', 'viewer') NOT NULL DEFAULT 'viewer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Alarms and Incident Management
CREATE TABLE IF NOT EXISTS alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME(3) NOT NULL,
    tag VARCHAR(64) NOT NULL,
    value DOUBLE NOT NULL,
    threshold DOUBLE NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'WARNING',
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by VARCHAR(64) NULL,
    INDEX idx_alarm_ts (ts),
    INDEX idx_alarm_tag (tag)
) ENGINE=InnoDB;
