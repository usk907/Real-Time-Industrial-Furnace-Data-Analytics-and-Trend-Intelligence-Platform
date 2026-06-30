-- Dynamic check to create TimescaleDB extension if available
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
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MAINTENANCE', 'INACTIVE')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS areas (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER REFERENCES plants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT unique_plant_area UNIQUE (plant_id, name)
);

CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    area_id INTEGER REFERENCES areas(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., 'DISTRIBUTION', 'SMS_SHOP', 'TURBINES'
    status VARCHAR(20) DEFAULT 'STOPPED' CHECK (status IN ('RUNNING', 'STOPPED', 'MAINTENANCE', 'ALARM')),
    CONSTRAINT unique_area_equipment UNIQUE (area_id, name)
);

CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., 'POWER', 'VOLTAGE', 'CURRENT', 'ACCUMULATOR', 'SETPOINT'
    register_address VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    nominal_min DOUBLE PRECISION,
    nominal_max DOUBLE PRECISION,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT unique_equipment_sensor UNIQUE (equipment_id, name)
);

-- -----------------------------------------------------
-- 3. Time-Series Tables (Hypertables if TimescaleDB loaded)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS sensor_readings (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    value DOUBLE PRECISION NOT NULL,
    quality VARCHAR(20) DEFAULT 'GOOD' CHECK (quality IN ('GOOD', 'BAD', 'SUSPECT')),
    status VARCHAR(20) DEFAULT 'OK' CHECK (status IN ('OK', 'HIGH_LIMIT', 'LOW_LIMIT', 'ERROR'))
);

CREATE TABLE IF NOT EXISTS alarms (
    id BIGSERIAL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    alarm_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    trigger_value DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ACKNOWLEDGED', 'CLEARED')),
    acknowledged_by VARCHAR(50),
    comments TEXT,
    PRIMARY KEY (id, time)
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL,
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'INFO',
    PRIMARY KEY (id, time)
);

CREATE TABLE IF NOT EXISTS predictions (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    prediction_horizon_minutes INTEGER NOT NULL,
    sensor_id INTEGER REFERENCES sensors(id) ON DELETE CASCADE,
    predicted_value DOUBLE PRECISION NOT NULL,
    upper_bound DOUBLE PRECISION,
    lower_bound DOUBLE PRECISION,
    PRIMARY KEY (time, prediction_horizon_minutes, sensor_id)
);

CREATE TABLE IF NOT EXISTS kpi_history (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    equipment_id INTEGER REFERENCES equipment(id) ON DELETE CASCADE,
    kpi_name VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(20),
    PRIMARY KEY (time, equipment_id, kpi_name)
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    name VARCHAR(150) NOT NULL,
    report_type VARCHAR(20) CHECK (report_type IN ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY')),
    format VARCHAR(10) CHECK (format IN ('PDF', 'EXCEL', 'CSV')),
    file_path VARCHAR(255) NOT NULL
);

-- -----------------------------------------------------
-- 4. Enable TimescaleDB Hypertables (Conditional wrapper)
-- -----------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        PERFORM create_hypertable('sensor_readings', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);
        PERFORM create_hypertable('alarms', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);
        PERFORM create_hypertable('events', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);
        PERFORM create_hypertable('predictions', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);
        PERFORM create_hypertable('kpi_history', 'time', chunk_time_interval => INTERVAL '30 days', if_not_exists => TRUE);
        RAISE NOTICE 'Hypertables initialized successfully.';
    ELSE
        RAISE NOTICE 'Skipping hypertables initialization: TimescaleDB extension is not active.';
    END IF;
END $$;

-- -----------------------------------------------------
-- 5. Primary Indexing Optimization
-- -----------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_sensor_readings_id_time ON sensor_readings (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_alarms_sensor_time ON alarms (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_lookup ON predictions (sensor_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_kpis_eq_time ON kpi_history (equipment_id, kpi_name, time DESC);

-- -----------------------------------------------------
-- 6. Initial Seed Data matching user screenshots
-- -----------------------------------------------------

-- Insert Default Roles
INSERT INTO roles (name, permissions) VALUES
('Administrator', ARRAY['read_all', 'write_all', 'manage_users', 'acknowledge_alarms']),
('Plant Engineer', ARRAY['read_all', 'write_all', 'acknowledge_alarms']),
('Operator', ARRAY['read_all', 'acknowledge_alarms']),
('Viewer', ARRAY['read_all'])
ON CONFLICT (name) DO NOTHING;

-- Seed Default Admin User
INSERT INTO users (username, email, password_hash, role_id, is_active) VALUES
('admin', 'admin@industrial-analytics.com', '$2b$12$4O6lXWjX47.dJp8Xy4eB2OnX4m9/k93lqGheUa1s9p9Qx.J/3aK62', 1, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Seed Gary Steel Works
INSERT INTO plants (name, location, status) VALUES
('Gary Steel Works', 'Gary, Indiana', 'ACTIVE')
ON CONFLICT (name) DO NOTHING;

-- Seed Areas
INSERT INTO areas (plant_id, name, description) VALUES
(1, 'Power Distribution', 'Main substations, circuit breakers, and grid parameters'),
(1, 'Steel Melting Shop (SMS)', 'Electric Arc Furnaces and Ladle heating facilities')
ON CONFLICT ON CONSTRAINT unique_plant_area DO NOTHING;

-- Seed Equipment
INSERT INTO equipment (area_id, name, type, status) VALUES
(1, 'Distribution-System', 'DISTRIBUTION', 'RUNNING'),
(2, 'SMS-1', 'SMS_SHOP', 'RUNNING'),
(2, 'SMS-2', 'SMS_SHOP', 'RUNNING'),
(2, 'SMS-4', 'SMS_SHOP', 'RUNNING'),
(1, 'Turbines', 'TURBINES', 'RUNNING')
ON CONFLICT ON CONSTRAINT unique_area_equipment DO NOTHING;

-- Seed Sensors (ID 1-16: Distribution Panel)
INSERT INTO sensors (id, equipment_id, name, type, register_address, unit, nominal_min, nominal_max) VALUES
(1, 1, 'CB5214 kW', 'POWER', '30001', 'kW', 0.0, 50000.0),
(2, 1, 'CB14 kW', 'POWER', '30002', 'kW', 0.0, 50000.0),
(3, 1, 'CB52G4 kW', 'POWER', '30003', 'kW', 0.0, 30000.0),
(4, 1, 'CB52G14 kW', 'POWER', '30004', 'kW', 0.0, 30000.0),
(5, 1, 'CB52G24 kW', 'POWER', '30005', 'kW', 0.0, 30000.0),
(6, 1, 'SMS Allocated Power', 'POWER', '30006', 'kW', 0.0, 150000.0),
(7, 1, 'SMS Run. Power', 'POWER', '30007', 'kW', 0.0, 150000.0),
(8, 1, 'SMS-1 PR', 'SETPOINT', '30008', '', 0.0, 5.0),
(9, 1, 'SMS-2 PR', 'SETPOINT', '30009', '', 0.0, 5.0),
(10, 1, 'SMS-4 PR', 'SETPOINT', '30010', '', 0.0, 5.0),
(11, 1, 'SMS-1 Max Set', 'SETPOINT', '30011', 'kW', 0.0, 100000.0),
(12, 1, 'SMS-1 Min Set', 'SETPOINT', '30012', 'kW', 0.0, 50000.0),
(13, 1, 'SMS-2 Max Set', 'SETPOINT', '30013', 'kW', 0.0, 100000.0),
(14, 1, 'SMS-2 Min Set', 'SETPOINT', '30014', 'kW', 0.0, 50000.0),
(15, 1, 'SMS-4 Max Set', 'SETPOINT', '30015', 'kW', 0.0, 100000.0),
(16, 1, 'SMS-4 Min Set', 'SETPOINT', '30016', 'kW', 0.0, 50000.0)
ON CONFLICT (id) DO NOTHING;

-- Seed Sensors (ID 17-19: SMS-1 Furnace Parameters)
INSERT INTO sensors (id, equipment_id, name, type, register_address, unit, nominal_min, nominal_max) VALUES
(17, 2, 'SMS-1 Max Set', 'SETPOINT', '31001', 'kW', 0.0, 100000.0),
(18, 2, 'SMS-1 Avl. Power', 'POWER', '31002', 'kW', 0.0, 100000.0),
(19, 2, 'SMS-1 Run. Power', 'POWER', '31003', 'kW', 0.0, 100000.0)
ON CONFLICT (id) DO NOTHING;

-- Seed Sensors (ID 20-39: SMS-4 Furnace Details)
INSERT INTO sensors (id, equipment_id, name, type, register_address, unit, nominal_min, nominal_max) VALUES
(20, 4, 'SMS-4 Max Set', 'SETPOINT', '32001', 'kW', 0.0, 50000.0),
(21, 4, 'SMS-4 Avl. Power', 'POWER', '32002', 'kW', 0.0, 50000.0),
(22, 4, 'SMS-4 Run. Power', 'POWER', '32003', 'kW', 0.0, 50000.0),
(23, 4, 'SMS-4 Utl. Factor(%)', 'KPI', '32004', '%', 0.0, 100.0),
(24, 4, 'SMS-4 Fur-1 SP', 'SETPOINT', '32005', 'kW', 0.0, 10000.0),
(25, 4, 'SMS-4 Fur-1 kW', 'POWER', '32006', 'kW', 0.0, 10000.0),
(26, 4, 'SMS-4 Fur-1 PP%', 'POWER', '32007', '%', 0.0, 100.0),
(27, 4, 'SMS-4 Fur-1 PR', 'SETPOINT', '32008', '', 1.0, 4.0),
(28, 4, 'SMS-4 Fur-2 SP', 'SETPOINT', '32009', 'kW', 0.0, 10000.0),
(29, 4, 'SMS-4 Fur-2 kW', 'POWER', '32010', 'kW', 0.0, 10000.0),
(30, 4, 'SMS-4 Fur-2 PP%', 'POWER', '32011', '%', 0.0, 100.0),
(31, 4, 'SMS-4 Fur-2 PR', 'SETPOINT', '32012', '', 1.0, 4.0),
(32, 4, 'SMS-4 Fur-3 SP', 'SETPOINT', '32013', 'kW', 0.0, 10000.0),
(33, 4, 'SMS-4 Fur-3 kW', 'POWER', '32014', 'kW', 0.0, 10000.0),
(34, 4, 'SMS-4 Fur-3 PP%', 'POWER', '32015', '%', 0.0, 100.0),
(35, 4, 'SMS-4 Fur-3 PR', 'SETPOINT', '32016', '', 1.0, 4.0),
(36, 4, 'SMS-4 Fur-4 SP', 'SETPOINT', '32017', 'kW', 0.0, 10000.0),
(37, 4, 'SMS-4 Fur-4 kW', 'POWER', '32018', 'kW', 0.0, 10000.0),
(38, 4, 'SMS-4 Fur-4 PP%', 'POWER', '32019', '%', 0.0, 100.0),
(39, 4, 'SMS-4 Fur-4 PR', 'SETPOINT', '32020', '', 1.0, 4.0)
ON CONFLICT (id) DO NOTHING;

-- Seed Sensors (ID 40-44: Turbine Generators)
INSERT INTO sensors (id, equipment_id, name, type, register_address, unit, nominal_min, nominal_max) VALUES
(40, 5, '30MW TG-1 kW', 'POWER', '33001', 'kW', 0.0, 30000.0),
(41, 5, '30MW TG-2 kW', 'POWER', '33002', 'kW', 0.0, 30000.0),
(42, 5, '33MW TG-3 kW', 'POWER', '33003', 'kW', 0.0, 33000.0),
(43, 5, '30MW TG-4 kW', 'POWER', '33004', 'kW', 0.0, 30000.0),
(44, 5, '40MW TG-5 kW', 'POWER', '33005', 'kW', 0.0, 40000.0)
ON CONFLICT (id) DO NOTHING;

-- Seed Sensors (ID 45-50: Consumption Indices & Factors)
INSERT INTO sensors (id, equipment_id, name, type, register_address, unit, nominal_min, nominal_max) VALUES
(45, 1, 'Grid Import kWh', 'ACCUMULATOR', '34001', 'kWh', 0.0, 1000000.0),
(46, 1, 'Grid Import kVah', 'ACCUMULATOR', '34002', 'kVah', 0.0, 1000000.0),
(47, 1, 'Avg. P.F.', 'KPI', '34003', '', 0.0, 1.0),
(48, 1, 'Load Factor', 'KPI', '34004', '', 0.0, 100.0),
(49, 1, 'Grid Export kWh', 'ACCUMULATOR', '34005', 'kWh', 0.0, 1000000.0),
(50, 1, 'Grid Export kVah', 'ACCUMULATOR', '34006', 'kVah', 0.0, 1000000.0)
ON CONFLICT (id) DO NOTHING;
