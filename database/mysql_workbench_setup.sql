-- ====================================================================
-- IEIP SCADA PLATFORM & TAP SERVER: COMPLETE MYSQL DATABASE SETUP SCRIPT
-- Tested for: MySQL 8.0+, MySQL Workbench, MariaDB
-- ====================================================================

-- 1. Create and select the database
CREATE DATABASE IF NOT EXISTS furnace_db 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE furnace_db;

-- 2. Drop existing tables if re-initializing (safe order respecting foreign keys)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS tap_telemetry_readings;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS energy_reports;
DROP TABLE IF EXISTS settings;
DROP TABLE IF EXISTS kpi_history;
DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS alarms;
DROP TABLE IF EXISTS sensor_readings;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS machines;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS plants;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------
-- 3. Core Role-Based Access Control (RBAC) Tables
-- -----------------------------------------------------
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    permissions JSON
) ENGINE=InnoDB;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- 4. Plant Metadata Hierarchy
-- -----------------------------------------------------
CREATE TABLE plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(150),
    timezone VARCHAR(50) DEFAULT 'UTC',
    description TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plant_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT fk_dept_plant FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE,
    CONSTRAINT uq_plant_dept UNIQUE (plant_id, name)
) ENGINE=InnoDB;

CREATE TABLE machines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g. 'BREAKER', 'FURNACE', 'TURBINE'
    rated_capacity DOUBLE DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'STOPPED', -- 'RUNNING', 'STOPPED', 'MAINTENANCE', 'ALARM'
    CONSTRAINT fk_mach_dept FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    CONSTRAINT uq_dept_machine UNIQUE (department_id, name)
) ENGINE=InnoDB;

CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    machine_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    register_address VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    nominal_min DOUBLE,
    nominal_max DOUBLE,
    serial_number VARCHAR(100),
    firmware_version VARCHAR(50),
    communication_status VARCHAR(20) DEFAULT 'ONLINE',
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    installation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_dev_mach FOREIGN KEY (machine_id) REFERENCES machines(id) ON DELETE CASCADE,
    CONSTRAINT uq_mach_device UNIQUE (machine_id, name)
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- 5. Time-Series Telemetry & Operational Tables
-- -----------------------------------------------------
CREATE TABLE sensor_readings (
    time DATETIME NOT NULL,
    sensor_id INT NOT NULL,
    value DOUBLE NOT NULL,
    quality VARCHAR(20) DEFAULT 'GOOD',
    status VARCHAR(20) DEFAULT 'OK',
    PRIMARY KEY (time, sensor_id),
    CONSTRAINT fk_readings_dev FOREIGN KEY (sensor_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- TAP Server Dedicated Raw Ingestion Table
CREATE TABLE tap_telemetry_readings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    time DATETIME NOT NULL,
    sensor_id INT NOT NULL,
    sensor_name VARCHAR(100) NOT NULL,
    plant VARCHAR(100) DEFAULT 'Gary Steel Works',
    unit VARCHAR(20) DEFAULT '',
    value DOUBLE NOT NULL,
    quality VARCHAR(20) DEFAULT 'GOOD',
    status VARCHAR(20) DEFAULT 'OK',
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tap_time (time),
    INDEX idx_tap_sensor (sensor_id)
) ENGINE=InnoDB;

CREATE TABLE alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL,
    sensor_id INT NOT NULL,
    alarm_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'CRITICAL', 'WARNING', 'INFO'
    trigger_value DOUBLE,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'ACKNOWLEDGED', 'CLEARED'
    acknowledged_by VARCHAR(50),
    comments TEXT,
    CONSTRAINT fk_alarms_dev FOREIGN KEY (sensor_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    time DATETIME DEFAULT CURRENT_TIMESTAMP,
    equipment_id INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'INFO',
    CONSTRAINT fk_events_mach FOREIGN KEY (equipment_id) REFERENCES machines(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE predictions (
    time DATETIME NOT NULL,
    prediction_horizon_minutes INT NOT NULL,
    sensor_id INT NOT NULL,
    predicted_value DOUBLE NOT NULL,
    upper_bound DOUBLE,
    lower_bound DOUBLE,
    PRIMARY KEY (time, prediction_horizon_minutes, sensor_id),
    CONSTRAINT fk_pred_dev FOREIGN KEY (sensor_id) REFERENCES devices(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE kpi_history (
    time DATETIME NOT NULL,
    equipment_id INT NOT NULL,
    kpi_name VARCHAR(50) NOT NULL,
    value DOUBLE NOT NULL,
    unit VARCHAR(20),
    PRIMARY KEY (time, equipment_id, kpi_name),
    CONSTRAINT fk_kpi_mach FOREIGN KEY (equipment_id) REFERENCES machines(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE settings (
    `key` VARCHAR(100) PRIMARY KEY,
    `value` VARCHAR(255) NOT NULL,
    description TEXT
) ENGINE=InnoDB;

CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE energy_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_date VARCHAR(20) NOT NULL,
    shift VARCHAR(10) NOT NULL,
    source_filename VARCHAR(255),
    total_active_kwh DOUBLE DEFAULT 0.0,
    total_apparent_kvah DOUBLE DEFAULT 0.0,
    total_reactive_kvarh DOUBLE DEFAULT 0.0,
    peak_demand_kw DOUBLE DEFAULT 0.0,
    avg_power_factor DOUBLE DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- -----------------------------------------------------
-- 6. Initial Master Data Seeding
-- -----------------------------------------------------

-- Insert Default Roles
INSERT INTO roles (id, name, permissions) VALUES
(1, 'Admin', '["*"]'),
(2, 'Plant Manager', '["plants:read", "plants:write", "machines:read", "machines:write", "alarms:read", "alarms:write", "reports:read"]'),
(3, 'Engineer', '["plants:read", "machines:read", "devices:read", "devices:write", "alarms:read", "alarms:write", "reports:read"]'),
(4, 'Operator', '["plants:read", "machines:read", "devices:read", "alarms:read", "alarms:write"]'),
(5, 'Viewer', '["plants:read", "machines:read", "devices:read", "reports:read"]');

-- Insert Default Admin User (Password: admin123)
INSERT INTO users (id, username, email, password_hash, role_id, is_active) VALUES
(1, 'admin', 'admin@ieip.local', '$2b$12$6/7a2s9/4KxLp8k0Z51VreWp2V.E6h9v7sW4.aC6fL8/5f3Z.4Fma', 1, TRUE);

-- Insert Gary Steel Works Plant
INSERT INTO plants (id, name, location, timezone, description, status) VALUES
(1, 'Gary Steel Works', 'Gary, Indiana, USA', 'America/Chicago', 'Integrated primary blast furnace and steel manufacturing complex with captive thermal power generation.', 'ACTIVE');

-- Insert Departments
INSERT INTO departments (id, plant_id, name, description) VALUES
(1, 1, 'SMS Steel Melting Shop', 'Electric Arc Furnaces (EAF), Ladle Refining, and Continuous Casting facility.'),
(2, 1, 'Captive Power Plant', 'Turbine generators, waste heat recovery, and high voltage transmission distribution.');

-- Insert Machines / Units
INSERT INTO machines (id, department_id, name, type, rated_capacity, status) VALUES
(1, 2, 'Main Distribution Breakers', 'BREAKER', 120000.0, 'RUNNING'),
(2, 1, 'SMS-1 Primary Furnace Line', 'FURNACE', 70000.0, 'RUNNING'),
(3, 1, 'SMS-4 Multi-Furnace Cell', 'FURNACE', 30000.0, 'RUNNING'),
(4, 2, '30MW Turbine Generator TG-2', 'TURBINE', 30000.0, 'RUNNING'),
(5, 2, '33MW Turbine Generator TG-3', 'TURBINE', 33000.0, 'RUNNING');

-- Insert All 60 Industrial Devices / Sensors
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, communication_status, is_active) VALUES
(1, 1, 'CB5214 kW', 'POWER', '40001', 'kW', 0.0, 50000.0, 'ONLINE', TRUE),
(2, 1, 'CB14 kW', 'POWER', '40002', 'kW', 0.0, 45000.0, 'ONLINE', TRUE),
(3, 1, 'CB52G4 kW', 'POWER', '40003', 'kW', 0.0, 30000.0, 'ONLINE', TRUE),
(4, 1, 'CB52G14 kW', 'POWER', '40004', 'kW', 0.0, 1000.0, 'ONLINE', TRUE),
(5, 1, 'CB52G24 kW', 'POWER', '40005', 'kW', 0.0, 1000.0, 'ONLINE', TRUE),
(6, 1, 'SMS Allocated Power', 'POWER', '40006', 'kW', 0.0, 120000.0, 'ONLINE', TRUE),
(7, 1, 'SMS Run. Power', 'POWER', '40007', 'kW', 0.0, 100000.0, 'ONLINE', TRUE),
(8, 2, 'SMS-1 PR', 'SETPOINT', '40008', '', 0.0, 5.0, 'ONLINE', TRUE),
(9, 2, 'SMS-2 PR', 'SETPOINT', '40009', '', 0.0, 5.0, 'ONLINE', TRUE),
(10, 3, 'SMS-4 PR', 'SETPOINT', '40010', '', 0.0, 5.0, 'ONLINE', TRUE),
(11, 2, 'SMS-1 Max Set', 'SETPOINT', '40011', 'kW', 0.0, 75000.0, 'ONLINE', TRUE),
(12, 2, 'SMS-1 Min Set', 'SETPOINT', '40012', 'kW', 0.0, 40000.0, 'ONLINE', TRUE),
(13, 2, 'SMS-2 Max Set', 'SETPOINT', '40013', 'kW', 0.0, 1000.0, 'ONLINE', TRUE),
(14, 2, 'SMS-2 Min Set', 'SETPOINT', '40014', 'kW', 0.0, 1000.0, 'ONLINE', TRUE),
(15, 3, 'SMS-4 Max Set', 'SETPOINT', '40015', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(16, 3, 'SMS-4 Min Set', 'SETPOINT', '40016', 'kW', 0.0, 20000.0, 'ONLINE', TRUE),
(17, 2, 'SMS-1 Max Set Active', 'POWER', '40017', 'kW', 0.0, 75000.0, 'ONLINE', TRUE),
(18, 2, 'SMS-1 Avl. Power', 'POWER', '40018', 'kW', 0.0, 75000.0, 'ONLINE', TRUE),
(19, 2, 'SMS-1 Run. Power', 'POWER', '40019', 'kW', 0.0, 70000.0, 'ONLINE', TRUE),
(20, 3, 'SMS-4 Max Set Active', 'POWER', '40020', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(21, 3, 'SMS-4 Avl. Power', 'POWER', '40021', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(22, 3, 'SMS-4 Run. Power', 'POWER', '40022', 'kW', 0.0, 30000.0, 'ONLINE', TRUE),
(23, 3, 'SMS-4 Utl. Factor(%)', 'EFFICIENCY', '40023', '%', 0.0, 100.0, 'ONLINE', TRUE),
(24, 3, 'SMS-4 Fur-1 SP', 'SETPOINT', '40024', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(25, 3, 'SMS-4 Fur-1 kW', 'POWER', '40025', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(26, 3, 'SMS-4 Fur-1 PP%', 'EFFICIENCY', '40026', '%', 0.0, 100.0, 'ONLINE', TRUE),
(27, 3, 'SMS-4 Fur-1 PR', 'SETPOINT', '40027', '', 0.0, 5.0, 'ONLINE', TRUE),
(28, 3, 'SMS-4 Fur-2 SP', 'SETPOINT', '40028', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(29, 3, 'SMS-4 Fur-2 kW', 'POWER', '40029', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(30, 3, 'SMS-4 Fur-2 PP%', 'EFFICIENCY', '40030', '%', 0.0, 100.0, 'ONLINE', TRUE),
(31, 3, 'SMS-4 Fur-2 PR', 'SETPOINT', '40031', '', 0.0, 5.0, 'ONLINE', TRUE),
(32, 3, 'SMS-4 Fur-3 SP', 'SETPOINT', '40032', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(33, 3, 'SMS-4 Fur-3 kW', 'POWER', '40033', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(34, 3, 'SMS-4 Fur-3 PP%', 'EFFICIENCY', '40034', '%', 0.0, 100.0, 'ONLINE', TRUE),
(35, 3, 'SMS-4 Fur-3 PR', 'SETPOINT', '40035', '', 0.0, 5.0, 'ONLINE', TRUE),
(36, 3, 'SMS-4 Fur-4 SP', 'SETPOINT', '40036', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(37, 3, 'SMS-4 Fur-4 kW', 'POWER', '40037', 'kW', 0.0, 10000.0, 'ONLINE', TRUE),
(38, 3, 'SMS-4 Fur-4 PP%', 'EFFICIENCY', '40038', '%', 0.0, 100.0, 'ONLINE', TRUE),
(39, 3, 'SMS-4 Fur-4 PR', 'SETPOINT', '40039', '', 0.0, 5.0, 'ONLINE', TRUE),
(40, 4, '30MW TG-1 kW', 'POWER', '40040', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(41, 4, '30MW TG-2 kW', 'POWER', '40041', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(42, 5, '33MW TG-3 kW', 'POWER', '40042', 'kW', 0.0, 38000.0, 'ONLINE', TRUE),
(43, 4, '30MW TG-4 kW', 'POWER', '40043', 'kW', 0.0, 35000.0, 'ONLINE', TRUE),
(44, 5, '40MW TG-5 kW', 'POWER', '40044', 'kW', 0.0, 45000.0, 'ONLINE', TRUE),
(45, 1, 'Grid Import kWh', 'ACCUMULATOR', '40045', 'kWh', 0.0, 10000000.0, 'ONLINE', TRUE),
(46, 1, 'Grid Import kVah', 'ACCUMULATOR', '40046', 'kVah', 0.0, 10000000.0, 'ONLINE', TRUE),
(47, 1, 'Avg. P.F.', 'POWER_FACTOR', '40047', '', 0.5, 1.0, 'ONLINE', TRUE),
(48, 1, 'Load Factor', 'EFFICIENCY', '40048', '%', 0.0, 100.0, 'ONLINE', TRUE),
(49, 1, 'Grid Export kWh', 'ACCUMULATOR', '40049', 'kWh', 0.0, 10000000.0, 'ONLINE', TRUE),
(50, 1, 'Grid Export kVah', 'ACCUMULATOR', '40050', 'kVah', 0.0, 10000000.0, 'ONLINE', TRUE),
(51, 2, 'SMS-1 Furnace Temp', 'TEMPERATURE', '40051', '°C', 200.0, 1800.0, 'ONLINE', TRUE),
(52, 2, 'SMS-1 Furnace Pressure', 'PRESSURE', '40052', 'bar', 0.0, 5.0, 'ONLINE', TRUE),
(53, 2, 'SMS-1 Cooling Water Flow', 'FLOW', '40053', 'm³/h', 0.0, 500.0, 'ONLINE', TRUE),
(54, 4, 'TG-2 Turbine RPM', 'SPEED', '40054', 'RPM', 0.0, 4500.0, 'ONLINE', TRUE),
(55, 1, 'CB5214 Voltage', 'VOLTAGE', '40055', 'V', 0.0, 15000.0, 'ONLINE', TRUE),
(56, 1, 'CB5214 Current', 'CURRENT', '40056', 'A', 0.0, 500.0, 'ONLINE', TRUE),
(57, 2, 'SMS Ambient Humidity', 'HUMIDITY', '40057', '%', 0.0, 100.0, 'ONLINE', TRUE),
(58, 2, 'SMS Carbon Dioxide (CO2)', 'GAS', '40058', 'ppm', 0.0, 2000.0, 'ONLINE', TRUE),
(59, 2, 'SMS-1 Production Count', 'COUNT', '40059', 'heats', 0.0, 1000.0, 'ONLINE', TRUE),
(60, 3, 'SMS-4 Gas Level (CO)', 'GAS', '40060', 'ppm', 0.0, 100.0, 'ONLINE', TRUE);

-- Insert Default System Settings & Thresholds
INSERT INTO settings (`key`, `value`, description) VALUES
('alarm_threshold_breaker_max', '45000.0', 'Maximum continuous power trip limit for Circuit Breaker CB5214 in kW'),
('alarm_threshold_tg_max', '30000.0', 'Maximum generator capacity threshold for TG-2 and TG-3 turbines in kW'),
('alarm_threshold_sms_max', '95000.0', 'Total allocated power surge ceiling for SMS shop running power in kW'),
('ENERGY_TARIFF_INR_PER_KWH', '7.50', 'Industrial electricity tariff rate in INR per active kWh'),
('CO2_EMISSION_FACTOR_KG_PER_KWH', '0.82', 'Grid carbon emissions conversion factor in kg CO2 per kWh');

-- Done!
SELECT 'Database furnace_db and all 15 tables created & seeded successfully!' AS status;
