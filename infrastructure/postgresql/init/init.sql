-- ==========================================
-- CyberShield Data Platform
-- Database Initialization
-- ==========================================

-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Pipelines Table
CREATE TABLE IF NOT EXISTS pipelines (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Pipeline Runs Table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id SERIAL PRIMARY KEY,
    pipeline_id INTEGER REFERENCES pipelines(id),
    status VARCHAR(20),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INTEGER
);

-- Create Settings Table
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE,
    setting_value TEXT
);

-- Create Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- Default Administrator
-- ==========================================

INSERT INTO users (username, email, password_hash, role)
VALUES (
    'admin',
    'admin@cybershield.local',
    'admin123',
    'admin'
)
ON CONFLICT (email) DO NOTHING;

-- ==========================================
-- Default Pipeline
-- ==========================================

INSERT INTO pipelines (pipeline_name, description, status)
VALUES (
    'Cyber Data Ingestion',
    'Real-time ingestion from Kafka',
    'active'
)
ON CONFLICT DO NOTHING; 

-- ==========================================
-- Security Events Table (Silver → PostgreSQL)
-- ==========================================

CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL,
    event_type VARCHAR(100),
    severity VARCHAR(20),
    timestamp TIMESTAMPTZ NOT NULL,
    event_date DATE,
    event_hour INTEGER,
    source_ip TEXT,
    destination_ip TEXT,
    protocol VARCHAR(20),
    source_port INTEGER,
    destination_port INTEGER,
    processed_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_event_date ON security_events(event_date);

-- ==========================================
-- Security Event ML Table (Machine Learning Output)
-- ==========================================

CREATE TABLE IF NOT EXISTS security_event_ml (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL REFERENCES security_events(event_id) ON DELETE CASCADE,
    risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    is_anomaly BOOLEAN NOT NULL,
    model_version VARCHAR(50) DEFAULT 'v1.0.0',
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ml_risk_level ON security_event_ml(risk_level);
CREATE INDEX IF NOT EXISTS idx_ml_is_anomaly ON security_event_ml(is_anomaly);