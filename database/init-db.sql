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
(1, 'Gary Steel Works', 'Gary, Indiana', 'EST', 'Primary integrated steel production mill', 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

-- Seed Departments
INSERT INTO departments (id, plant_id, name, description) VALUES
(1, 1, 'Power Distribution', 'Substations and distribution grids'),
(2, 1, 'Steel Melting Shop (SMS)', 'Electric Arc Furnace shops')
ON CONFLICT (id) DO NOTHING;

-- Seed Machines
INSERT INTO machines (id, department_id, name, type, rated_capacity, status) VALUES
(1, 1, 'Distribution-System', 'DISTRIBUTION', 150000.0, 'RUNNING'),
(2, 2, 'SMS-1', 'SMS_SHOP', 70000.0, 'RUNNING'),
(3, 2, 'SMS-2', 'SMS_SHOP', 70000.0, 'STOPPED'),
(4, 2, 'SMS-4', 'SMS_SHOP', 30000.0, 'RUNNING'),
(5, 1, 'Turbines', 'TURBINES', 63000.0, 'RUNNING')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (Grid & Distribution, machine_id = 1)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(1, 1, 'CB5214 kW', 'POWER', '30001', 'kW', 0.0, 50000.0, 'SN-CB5214', 'v1.4.2', 'ONLINE', '2024-01-15'),
(2, 1, 'CB14 kW', 'POWER', '30002', 'kW', 0.0, 50000.0, 'SN-CB14', 'v1.4.2', 'ONLINE', '2024-01-15'),
(3, 1, 'CB52G4 kW', 'POWER', '30003', 'kW', 0.0, 30000.0, 'SN-CB52G4', 'v1.3.1', 'ONLINE', '2024-02-10'),
(4, 1, 'CB52G14 kW', 'POWER', '30004', 'kW', 0.0, 30000.0, 'SN-CB52G14', 'v1.3.1', 'ONLINE', '2024-02-10'),
(5, 1, 'CB52G24 kW', 'POWER', '30005', 'kW', 0.0, 30000.0, 'SN-CB52G24', 'v1.3.1', 'ONLINE', '2024-02-10'),
(6, 1, 'SMS Allocated Power', 'POWER', '30006', 'kW', 0.0, 150000.0, 'SN-SMS-AL', 'v2.0.1', 'ONLINE', '2023-11-05'),
(7, 1, 'SMS Run. Power', 'POWER', '30007', 'kW', 0.0, 150000.0, 'SN-SMS-RN', 'v2.0.1', 'ONLINE', '2023-11-05'),
(8, 1, 'SMS-1 PR', 'SETPOINT', '30008', '', 0.0, 5.0, 'SN-SMS1PR', 'v1.0.0', 'ONLINE', '2024-03-01'),
(9, 1, 'SMS-2 PR', 'SETPOINT', '30009', '', 0.0, 5.0, 'SN-SMS2PR', 'v1.0.0', 'ONLINE', '2024-03-01'),
(10, 1, 'SMS-4 PR', 'SETPOINT', '30010', '', 0.0, 5.0, 'SN-SMS4PR', 'v1.0.0', 'ONLINE', '2024-03-01'),
(11, 1, 'SMS-1 Max Set', 'SETPOINT', '30011', 'kW', 0.0, 100000.0, 'SN-SMS1MAX', 'v1.0.0', 'ONLINE', '2024-03-01'),
(12, 1, 'SMS-1 Min Set', 'SETPOINT', '30012', 'kW', 0.0, 50000.0, 'SN-SMS1MIN', 'v1.0.0', 'ONLINE', '2024-03-01'),
(13, 1, 'SMS-2 Max Set', 'SETPOINT', '30013', 'kW', 0.0, 100000.0, 'SN-SMS2MAX', 'v1.0.0', 'ONLINE', '2024-03-01'),
(14, 1, 'SMS-2 Min Set', 'SETPOINT', '30014', 'kW', 0.0, 50000.0, 'SN-SMS2MIN', 'v1.0.0', 'ONLINE', '2024-03-01'),
(15, 1, 'SMS-4 Max Set', 'SETPOINT', '30015', 'kW', 0.0, 100000.0, 'SN-SMS4MAX', 'v1.0.0', 'ONLINE', '2024-03-01'),
(16, 1, 'SMS-4 Min Set', 'SETPOINT', '30016', 'kW', 0.0, 50000.0, 'SN-SMS4MIN', 'v1.0.0', 'ONLINE', '2024-03-01')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (SMS-1 Furnace, machine_id = 2)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(17, 2, 'SMS-1 Max Set', 'SETPOINT', '31001', 'kW', 0.0, 100000.0, 'SN-SMS1F-MAX', 'v1.1.0', 'ONLINE', '2024-03-01'),
(18, 2, 'SMS-1 Avl. Power', 'POWER', '31002', 'kW', 0.0, 100000.0, 'SN-SMS1F-AVL', 'v1.1.0', 'ONLINE', '2024-03-01'),
(19, 2, 'SMS-1 Run. Power', 'POWER', '31003', 'kW', 0.0, 100000.0, 'SN-SMS1F-RUN', 'v1.1.0', 'ONLINE', '2024-03-01')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (SMS-4 Furnace, machine_id = 4)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(20, 4, 'SMS-4 Max Set', 'SETPOINT', '32001', 'kW', 0.0, 50000.0, 'SN-SMS4-MAX', 'v1.2.0', 'ONLINE', '2024-04-12'),
(21, 4, 'SMS-4 Avl. Power', 'POWER', '32002', 'kW', 0.0, 50000.0, 'SN-SMS4-AVL', 'v1.2.0', 'ONLINE', '2024-04-12'),
(22, 4, 'SMS-4 Run. Power', 'POWER', '32003', 'kW', 0.0, 50000.0, 'SN-SMS4-RUN', 'v1.2.0', 'ONLINE', '2024-04-12'),
(23, 4, 'SMS-4 Utl. Factor(%)', 'KPI', '32004', '%', 0.0, 100.0, 'SN-SMS4-UTL', 'v1.2.0', 'ONLINE', '2024-04-12'),
(24, 4, 'SMS-4 Fur-1 SP', 'SETPOINT', '32005', 'kW', 0.0, 10000.0, 'SN-SMS4-F1SP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(25, 4, 'SMS-4 Fur-1 kW', 'POWER', '32006', 'kW', 0.0, 10000.0, 'SN-SMS4-F1KW', 'v2.1.2', 'ONLINE', '2024-04-15'),
(26, 4, 'SMS-4 Fur-1 PP%', 'POWER', '32007', '%', 0.0, 100.0, 'SN-SMS4-F1PP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(27, 4, 'SMS-4 Fur-1 PR', 'SETPOINT', '32008', '', 1.0, 4.0, 'SN-SMS4-F1PR', 'v2.1.2', 'ONLINE', '2024-04-15'),
(28, 4, 'SMS-4 Fur-2 SP', 'SETPOINT', '32009', 'kW', 0.0, 10000.0, 'SN-SMS4-F2SP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(29, 4, 'SMS-4 Fur-2 kW', 'POWER', '32010', 'kW', 0.0, 10000.0, 'SN-SMS4-F2KW', 'v2.1.2', 'ONLINE', '2024-04-15'),
(30, 4, 'SMS-4 Fur-2 PP%', 'POWER', '32011', '%', 0.0, 100.0, 'SN-SMS4-F2PP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(31, 4, 'SMS-4 Fur-2 PR', 'SETPOINT', '32012', '', 1.0, 4.0, 'SN-SMS4-F2PR', 'v2.1.2', 'ONLINE', '2024-04-15'),
(32, 4, 'SMS-4 Fur-3 SP', 'SETPOINT', '32013', 'kW', 0.0, 10000.0, 'SN-SMS4-F3SP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(33, 4, 'SMS-4 Fur-3 kW', 'POWER', '32014', 'kW', 0.0, 10000.0, 'SN-SMS4-F3KW', 'v2.1.2', 'ONLINE', '2024-04-15'),
(34, 4, 'SMS-4 Fur-3 PP%', 'POWER', '32015', '%', 0.0, 100.0, 'SN-SMS4-F3PP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(35, 4, 'SMS-4 Fur-3 PR', 'SETPOINT', '32016', '', 1.0, 4.0, 'SN-SMS4-F3PR', 'v2.1.2', 'ONLINE', '2024-04-15'),
(36, 4, 'SMS-4 Fur-4 SP', 'SETPOINT', '32017', 'kW', 0.0, 10000.0, 'SN-SMS4-F4SP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(37, 4, 'SMS-4 Fur-4 kW', 'POWER', '32018', 'kW', 0.0, 10000.0, 'SN-SMS4-F4KW', 'v2.1.2', 'ONLINE', '2024-04-15'),
(38, 4, 'SMS-4 Fur-4 PP%', 'POWER', '32019', '%', 0.0, 100.0, 'SN-SMS4-F4PP', 'v2.1.2', 'ONLINE', '2024-04-15'),
(39, 4, 'SMS-4 Fur-4 PR', 'SETPOINT', '32020', '', 1.0, 4.0, 'SN-SMS4-F4PR', 'v2.1.2', 'ONLINE', '2024-04-15')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (Turbines, machine_id = 5)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(40, 5, '30MW TG-1 kW', 'POWER', '33001', 'kW', 0.0, 30000.0, 'SN-TG1', 'v3.2.0', 'ONLINE', '2022-06-18'),
(41, 5, '30MW TG-2 kW', 'POWER', '33002', 'kW', 0.0, 30000.0, 'SN-TG2', 'v3.2.0', 'ONLINE', '2022-06-18'),
(42, 5, '33MW TG-3 kW', 'POWER', '33003', 'kW', 0.0, 33000.0, 'SN-TG3', 'v3.2.5', 'ONLINE', '2022-08-22'),
(43, 5, '30MW TG-4 kW', 'POWER', '33004', 'kW', 0.0, 30000.0, 'SN-TG4', 'v3.2.0', 'ONLINE', '2022-06-18'),
(44, 5, '40MW TG-5 kW', 'POWER', '33005', 'kW', 0.0, 40000.0, 'SN-TG5', 'v3.5.0', 'ONLINE', '2023-05-12')
ON CONFLICT (id) DO NOTHING;

-- Seed Devices (Accumulators & KPIs, machine_id = 1)
INSERT INTO devices (id, machine_id, name, type, register_address, unit, nominal_min, nominal_max, serial_number, firmware_version, communication_status, installation_date) VALUES
(45, 1, 'Grid Import kWh', 'ACCUMULATOR', '34001', 'kWh', 0.0, 10000000.0, 'SN-MTR1', 'v2.1.0', 'ONLINE', '2024-01-15'),
(46, 1, 'Grid Import kVah', 'ACCUMULATOR', '34002', 'kVah', 0.0, 10000000.0, 'SN-MTR1', 'v2.1.0', 'ONLINE', '2024-01-15'),
(47, 1, 'Avg. P.F.', 'KPI', '34003', '', 0.0, 1.0, 'SN-MTR1', 'v2.1.0', 'ONLINE', '2024-01-15'),
(48, 1, 'Load Factor', 'KPI', '34004', '', 0.0, 100.0, 'SN-MTR1', 'v2.1.0', 'ONLINE', '2024-01-15'),
(49, 1, 'Grid Export kWh', 'ACCUMULATOR', '34005', 'kWh', 0.0, 10000000.0, 'SN-MTR2', 'v2.1.0', 'ONLINE', '2024-01-15'),
(50, 1, 'Grid Export kVah', 'ACCUMULATOR', '34006', 'kVah', 0.0, 10000000.0, 'SN-MTR2', 'v2.1.0', 'ONLINE', '2024-01-15')
ON CONFLICT (id) DO NOTHING;
