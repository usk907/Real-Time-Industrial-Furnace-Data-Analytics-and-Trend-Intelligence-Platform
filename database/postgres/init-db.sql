-- Create TimescaleDB extension if available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb') THEN
        CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    ELSE
        RAISE NOTICE 'TimescaleDB extension not available. System will run using vanilla PostgreSQL tables.';
    END IF;
END $$;

-- -----------------------------------------------------
-- 1. Roles and Users Tables
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    permissions TEXT[] DEFAULT '{}'::TEXT[]
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- 2. Metadata Tables: Plant hierarchy
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS plants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(150),
    timezone VARCHAR(50) DEFAULT 'UTC',
    description TEXT,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MAINTENANCE', 'INACTIVE')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER REFERENCES plants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT unique_plant_dept UNIQUE (plant_id, name)
);

CREATE TABLE IF NOT EXISTS machines (
    id SERIAL PRIMARY KEY,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., 'DISTRIBUTION', 'SMS_SHOP', 'TURBINES'
    rated_capacity DOUBLE PRECISION DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'STOPPED' CHECK (status IN ('RUNNING', 'STOPPED', 'MAINTENANCE', 'ALARM')),
    CONSTRAINT unique_dept_machine UNIQUE (department_id, name)
);

CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., 'POWER', 'VOLTAGE', 'CURRENT', 'TEMPERATURE', 'ACCUMULATOR', 'SETPOINT'
    register_address VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    nominal_min DOUBLE PRECISION,
    nominal_max DOUBLE PRECISION,
    serial_number VARCHAR(100),
    firmware_version VARCHAR(50),
    communication_status VARCHAR(20) DEFAULT 'ONLINE' CHECK (communication_status IN ('ONLINE', 'OFFLINE', 'FAULTY')),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    installation_date DATE DEFAULT CURRENT_DATE,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT unique_machine_device UNIQUE (machine_id, name)
);

-- -----------------------------------------------------
-- 3. Time-Series Tables
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL,
    quality VARCHAR(20) DEFAULT 'GOOD' CHECK (quality IN ('GOOD', 'BAD', 'SUSPECT')),
    status VARCHAR(20) DEFAULT 'OK' CHECK (status IN ('OK', 'HIGH_LIMIT', 'LOW_LIMIT', 'ERROR'))
);

CREATE TABLE IF NOT EXISTS alarms (
    id BIGSERIAL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    sensor_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    alarm_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    trigger_value DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ACKNOWLEDGED', 'CLEARED')),
    acknowledged_by VARCHAR(50),
    comments TEXT,
    PRIMARY KEY (id, time)
);

-- -----------------------------------------------------
-- 4. Audit, Notifications and Settings Tables
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45)
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'INFO', -- INFO, WARNING, ALARM
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value VARCHAR(255) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------
-- 5. Indexing Strategy
-- -----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sensor_readings_id_time ON sensor_readings (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_alarms_sensor_time ON alarms (sensor_id, time DESC);

-- -----------------------------------------------------
-- 6. Seed Initial Data
-- -----------------------------------------------------

-- Insert Default Roles
INSERT INTO roles (id, name, permissions) VALUES
(1, 'Admin', ARRAY['read_all', 'write_all', 'manage_users', 'acknowledge_alarms', 'manage_settings']),
(2, 'Plant Manager', ARRAY['read_all', 'write_all', 'acknowledge_alarms']),
(3, 'Engineer', ARRAY['read_all', 'acknowledge_alarms']),
(4, 'Operator', ARRAY['read_all', 'acknowledge_alarms']),
(5, 'Viewer', ARRAY['read_all'])
ON CONFLICT (name) DO NOTHING;

-- Seed Default Admin User (password: admin123)
-- Generated using bcrypt hash for 'admin123'
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
('admin', 'admin@ieip-platform.com', '$2b$12$R.S2uUuWf9Uq0L8M2c2j5uUoA8bS3q1WlQpUaOqF.4n5D5U5m2k5e', 1, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Seed Default settings
INSERT INTO settings (key, value, description) VALUES
('sampling_interval_seconds', '1', 'Sampling frequency of the telemetry ingestion'),
('alarm_threshold_breaker_max', '45000.0', 'Max breaker capacity for CB5214 (kW)'),
('alarm_threshold_tg_max', '30000.0', 'Max turbine power limit for 30MW TG-2 (kW)'),
('alarm_threshold_sms_max', '95000.0', 'Max threshold power for Steel Melting Shop combined load (kW)'),
('prediction_horizon_minutes', '60', 'ML Forecasting horizon window')
ON CONFLICT (key) DO NOTHING;

-- Seed Plant
INSERT INTO plants (id, name, location, timezone, description, status) VALUES
(1, 'Shyam Metaliks & Energy Ltd.', 'West Bengal, India', 'IST', 'Integrated steel and ferro alloys plant', 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

-- Seed Departments
INSERT INTO departments (id, plant_id, name, description) VALUES
(1, 1, 'Power Distribution', 'Substations and distribution grids'),
(2, 1, 'Steel Melting Shop (SMS)', 'Electric Arc Furnace shops'),
(3, 1, 'Ferro Alloys (SAF)', 'Submerged Arc Furnace shops'),
(4, 1, 'Rolling Mills', 'Rolling Mill mills')
ON CONFLICT (id) DO NOTHING;

-- Seed Machines
INSERT INTO machines (id, department_id, name, type, rated_capacity, status) VALUES
(1, 1, 'Distribution-System', 'DISTRIBUTION', 150000.0, 'RUNNING'),
(2, 2, 'SMS-1', 'SMS_SHOP', 70000.0, 'RUNNING'),
(3, 2, 'SMS-2', 'SMS_SHOP', 70000.0, 'STOPPED'),
(4, 2, 'SMS-4', 'SMS_SHOP', 30000.0, 'RUNNING'),
(5, 1, 'Turbines', 'TURBINES', 63000.0, 'RUNNING'),
(6, 3, 'SAF-Shop', 'FERRO_ALLOYS', 18000.0, 'RUNNING'),
(7, 4, 'Rolling-Mills', 'ROLLING_MILLS', 20000.0, 'RUNNING')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (Shyam Metaliks tags 1-48)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(1, 1, 'Grid Import kWh', 'ACCUMULATOR', '30001', 'kWh', 0.0, 10000000.0, 'SN-MTR1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(2, 1, 'Grid Import kVah', 'ACCUMULATOR', '30002', 'kVah', 0.0, 10000000.0, 'SN-MTR1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(3, 1, 'Grid Export kWh', 'ACCUMULATOR', '30003', 'kWh', 0.0, 10000000.0, 'SN-MTR2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(4, 1, 'Grid Export kVah', 'ACCUMULATOR', '30004', 'kVah', 0.0, 10000000.0, 'SN-MTR2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(5, 5, '30MW TG-1 kWh', 'ACCUMULATOR', '30005', 'kWh', 0.0, 10000000.0, 'SN-TG1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(6, 5, '30MW TG-2 kWh', 'ACCUMULATOR', '30006', 'kWh', 0.0, 10000000.0, 'SN-TG2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(7, 5, '33MW TG-3 kWh', 'ACCUMULATOR', '30007', 'kWh', 0.0, 10000000.0, 'SN-TG3', 'v1.0.0', 'ONLINE', '2026-06-30'),
(8, 5, '30MW TG-4 kWh', 'ACCUMULATOR', '30008', 'kWh', 0.0, 10000000.0, 'SN-TG4', 'v1.0.0', 'ONLINE', '2026-06-30'),
(9, 5, '40MW TG-5 kWh', 'ACCUMULATOR', '30009', 'kWh', 0.0, 10000000.0, 'SN-TG5', 'v1.0.0', 'ONLINE', '2026-06-30'),
(10, 2, 'SMS-1 Fur-1 kWh', 'ACCUMULATOR', '30010', 'kWh', 0.0, 10000000.0, 'SN-SMS1-F1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(11, 2, 'SMS-1 Fur-2 kWh', 'ACCUMULATOR', '30011', 'kWh', 0.0, 10000000.0, 'SN-SMS1-F2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(12, 2, 'SMS-1 Fur-3 kWh', 'ACCUMULATOR', '30012', 'kWh', 0.0, 10000000.0, 'SN-SMS1-F3', 'v1.0.0', 'ONLINE', '2026-06-30'),
(13, 2, 'SMS-1 Fur-4 kWh', 'ACCUMULATOR', '30013', 'kWh', 0.0, 10000000.0, 'SN-SMS1-F4', 'v1.0.0', 'ONLINE', '2026-06-30'),
(14, 2, 'SMS-1 Fur-5 kWh', 'ACCUMULATOR', '30014', 'kWh', 0.0, 10000000.0, 'SN-SMS1-F5', 'v1.0.0', 'ONLINE', '2026-06-30'),
(15, 2, 'SMS-1 Aux-1 kWh', 'ACCUMULATOR', '30015', 'kWh', 0.0, 10000000.0, 'SN-SMS1-A1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(16, 2, 'SMS-1 Aux-2 kWh', 'ACCUMULATOR', '30016', 'kWh', 0.0, 10000000.0, 'SN-SMS1-A2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(17, 2, 'SMS-1 Sint kWh', 'ACCUMULATOR', '30017', 'kWh', 0.0, 10000000.0, 'SN-SMS1-SINT', 'v1.0.0', 'ONLINE', '2026-06-30'),
(18, 6, 'SAF-1(2x9Mva) kWh', 'ACCUMULATOR', '30018', 'kWh', 0.0, 10000000.0, 'SN-SAF1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(19, 6, 'SAF-2(2x9Mva) kWh', 'ACCUMULATOR', '30019', 'kWh', 0.0, 10000000.0, 'SN-SAF2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(20, 6, 'SAF-3(2x4.5Mva) kWh', 'ACCUMULATOR', '30020', 'kWh', 0.0, 10000000.0, 'SN-SAF3', 'v1.0.0', 'ONLINE', '2026-06-30'),
(21, 7, 'RMD kWh', 'ACCUMULATOR', '30021', 'kWh', 0.0, 10000000.0, 'SN-RMD', 'v1.0.0', 'ONLINE', '2026-06-30'),
(22, 7, 'SRM kWh', 'ACCUMULATOR', '30022', 'kWh', 0.0, 10000000.0, 'SN-SRM', 'v1.0.0', 'ONLINE', '2026-06-30'),
(23, 7, 'WRM kWh', 'ACCUMULATOR', '30023', 'kWh', 0.0, 10000000.0, 'SN-WRM', 'v1.0.0', 'ONLINE', '2026-06-30'),
(24, 3, 'SMS-2 Fur-1 kWh', 'ACCUMULATOR', '30024', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(25, 3, 'SMS-2 Fur-2 kWh', 'ACCUMULATOR', '30025', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(26, 3, 'SMS-2 Fur-3 kWh', 'ACCUMULATOR', '30026', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F3', 'v1.0.0', 'ONLINE', '2026-06-30'),
(27, 3, 'SMS-2 Fur-4 kWh', 'ACCUMULATOR', '30027', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F4', 'v1.0.0', 'ONLINE', '2026-06-30'),
(28, 3, 'SMS-2 Fur-5 kWh', 'ACCUMULATOR', '30028', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F5', 'v1.0.0', 'ONLINE', '2026-06-30'),
(29, 3, 'SMS-2 Fur-6 kWh', 'ACCUMULATOR', '30029', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F6', 'v1.0.0', 'ONLINE', '2026-06-30'),
(30, 3, 'SMS-2 Fur-7 kWh', 'ACCUMULATOR', '30030', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F7', 'v1.0.0', 'ONLINE', '2026-06-30'),
(31, 3, 'SMS-2 Fur-8 kWh', 'ACCUMULATOR', '30031', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F8', 'v1.0.0', 'ONLINE', '2026-06-30'),
(32, 3, 'SMS-2 Fur-9 kWh', 'ACCUMULATOR', '30032', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F9', 'v1.0.0', 'ONLINE', '2026-06-30'),
(33, 3, 'SMS-2 Fur-10 kWh', 'ACCUMULATOR', '30033', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F10', 'v1.0.0', 'ONLINE', '2026-06-30'),
(34, 3, 'SMS-2 Fur-11 kWh', 'ACCUMULATOR', '30034', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F11', 'v1.0.0', 'ONLINE', '2026-06-30'),
(35, 3, 'SMS-2 Fur-12 kWh', 'ACCUMULATOR', '30035', 'kWh', 0.0, 10000000.0, 'SN-SMS2-F12', 'v1.0.0', 'ONLINE', '2026-06-30'),
(36, 4, 'SMS-4 Fur-1 kWh', 'ACCUMULATOR', '30036', 'kWh', 0.0, 10000000.0, 'SN-SMS4-F1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(37, 4, 'SMS-4 Fur-2 kWh', 'ACCUMULATOR', '30037', 'kWh', 0.0, 10000000.0, 'SN-SMS4-F2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(38, 4, 'SMS-4 Fur-3 kWh', 'ACCUMULATOR', '30038', 'kWh', 0.0, 10000000.0, 'SN-SMS4-F3', 'v1.0.0', 'ONLINE', '2026-06-30'),
(39, 4, 'SMS-4 Fur-4 kWh', 'ACCUMULATOR', '30039', 'kWh', 0.0, 10000000.0, 'SN-SMS4-F4', 'v1.0.0', 'ONLINE', '2026-06-30'),
(40, 3, 'SMS-2 Aux-1 kWh', 'ACCUMULATOR', '30040', 'kWh', 0.0, 10000000.0, 'SN-SMS2-A1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(41, 3, 'SMS-2 Aux-2 kWh', 'ACCUMULATOR', '30041', 'kWh', 0.0, 10000000.0, 'SN-SMS2-A2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(42, 4, 'SMS-4 Sint-1 kWh', 'ACCUMULATOR', '30042', 'kWh', 0.0, 10000000.0, 'SN-SMS4-SINT1', 'v1.0.0', 'ONLINE', '2026-06-30'),
(43, 4, 'SMS-4 Sint-2 kWh', 'ACCUMULATOR', '30043', 'kWh', 0.0, 10000000.0, 'SN-SMS4-SINT2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(44, 4, 'SMS-4 Aux kWh', 'ACCUMULATOR', '30044', 'kWh', 0.0, 10000000.0, 'SN-SMS4-AUX', 'v1.0.0', 'ONLINE', '2026-06-30'),
(45, 4, 'SMS-4 TR2MVA kWh', 'ACCUMULATOR', '30045', 'kWh', 0.0, 10000000.0, 'SN-SMS4-TR2', 'v1.0.0', 'ONLINE', '2026-06-30'),
(46, 4, 'SMS-4 TR6MVA kWh', 'ACCUMULATOR', '30046', 'kWh', 0.0, 10000000.0, 'SN-SMS4-TR6', 'v1.0.0', 'ONLINE', '2026-06-30'),
(47, 4, 'SMS-4 TR3.6MVA kWh', 'ACCUMULATOR', '30047', 'kWh', 0.0, 10000000.0, 'SN-SMS4-TR36', 'v1.0.0', 'ONLINE', '2026-06-30'),
(48, 4, 'SMS-4 TR5MVA kWh', 'ACCUMULATOR', '30048', 'kWh', 0.0, 10000000.0, 'SN-SMS4-TR5', 'v1.0.0', 'ONLINE', '2026-06-30')
ON CONFLICT (id) DO NOTHING;
