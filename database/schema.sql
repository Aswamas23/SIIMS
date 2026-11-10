-- SIIMS Database Schema
-- Run as PostgreSQL superuser or the siims_user (with CREATEDB permissions)
-- Tables listed in FK-dependency order

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'ict_technician',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    phone VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);
CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active);

-- ============================================================
-- REFRESH TOKENS
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jti VARCHAR(36) UNIQUE NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_jti ON refresh_tokens (jti);

-- ============================================================
-- LOCATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    building VARCHAR(100),
    floor VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_locations_name ON locations (name);

-- ============================================================
-- COMPUTERS
-- ============================================================
CREATE TABLE IF NOT EXISTS computers (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    mac_address VARCHAR(17) UNIQUE,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    processor VARCHAR(255),
    ram_gb INTEGER,
    storage_gb BIGINT,
    operating_system VARCHAR(255),
    os_version VARCHAR(255),
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    department VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    notes TEXT,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_computers_ip_address ON computers (ip_address);
CREATE INDEX IF NOT EXISTS ix_computers_status ON computers (status);
CREATE INDEX IF NOT EXISTS ix_computers_is_active ON computers (is_active);
CREATE INDEX IF NOT EXISTS ix_computers_location_id ON computers (location_id);
CREATE INDEX IF NOT EXISTS ix_computers_last_seen ON computers (last_seen);

-- ============================================================
-- AGENT CREDENTIALS
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_credentials (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    label VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_agent_credentials_computer_id ON agent_credentials (computer_id);
CREATE INDEX IF NOT EXISTS ix_agent_credentials_is_active ON agent_credentials (is_active);

-- ============================================================
-- HARDWARE METRICS
-- ============================================================
CREATE TABLE IF NOT EXISTS hardware_metrics (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cpu_percent FLOAT,
    cpu_freq_mhz FLOAT,
    cpu_count_logical INTEGER,
    cpu_temp_celsius FLOAT,
    ram_total_gb FLOAT,
    ram_used_gb FLOAT,
    ram_percent FLOAT,
    disk_total_gb FLOAT,
    disk_used_gb FLOAT,
    disk_free_gb FLOAT,
    disk_percent FLOAT,
    smart_status VARCHAR(50),
    uptime_seconds BIGINT,
    boot_time TIMESTAMPTZ,
    battery_percent FLOAT,
    battery_plugged BOOLEAN
);

CREATE INDEX IF NOT EXISTS ix_hardware_metrics_computer_id ON hardware_metrics (computer_id);
CREATE INDEX IF NOT EXISTS ix_hardware_metrics_recorded_at ON hardware_metrics (recorded_at);
CREATE INDEX IF NOT EXISTS ix_hardware_metrics_computer_recorded ON hardware_metrics (computer_id, recorded_at);

-- ============================================================
-- NETWORK METRICS
-- ============================================================
CREATE TABLE IF NOT EXISTS network_metrics (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interface_name VARCHAR(100),
    ip_address VARCHAR(45),
    mac_address VARCHAR(17),
    is_up BOOLEAN,
    gateway_reachable BOOLEAN,
    dns_resolves BOOLEAN,
    server_reachable BOOLEAN,
    latency_ms FLOAT,
    packet_loss_percent FLOAT,
    bytes_sent BIGINT,
    bytes_recv BIGINT
);

CREATE INDEX IF NOT EXISTS ix_network_metrics_computer_id ON network_metrics (computer_id);
CREATE INDEX IF NOT EXISTS ix_network_metrics_recorded_at ON network_metrics (recorded_at);
CREATE INDEX IF NOT EXISTS ix_network_metrics_computer_recorded ON network_metrics (computer_id, recorded_at);

-- ============================================================
-- INSTALLED SOFTWARE
-- ============================================================
CREATE TABLE IF NOT EXISTS installed_software (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    version VARCHAR(255),
    publisher VARCHAR(500),
    install_date DATE,
    install_location VARCHAR(1000),
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS ix_installed_software_computer_id ON installed_software (computer_id);
CREATE INDEX IF NOT EXISTS ix_installed_software_name ON installed_software (name);
CREATE INDEX IF NOT EXISTS ix_installed_software_last_seen ON installed_software (last_seen);
CREATE INDEX IF NOT EXISTS ix_installed_software_is_active ON installed_software (is_active);
CREATE INDEX IF NOT EXISTS ix_installed_software_computer_name ON installed_software (computer_id, name);

-- ============================================================
-- SOFTWARE LICENCES
-- ============================================================
CREATE TABLE IF NOT EXISTS software_licences (
    id SERIAL PRIMARY KEY,
    software_name VARCHAR(500) NOT NULL,
    version VARCHAR(255),
    licence_key TEXT,
    licence_type VARCHAR(100),
    vendor VARCHAR(500),
    seats INTEGER,
    purchase_date DATE,
    expiry_date DATE,
    cost INTEGER,
    notes TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_software_licences_expiry_date ON software_licences (expiry_date);
CREATE INDEX IF NOT EXISTS ix_software_licences_status ON software_licences (status);
CREATE INDEX IF NOT EXISTS ix_software_licences_is_active ON software_licences (is_active);

-- ============================================================
-- LICENCE ASSIGNMENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS licence_assignments (
    id SERIAL PRIMARY KEY,
    licence_id INTEGER NOT NULL REFERENCES software_licences(id) ON DELETE CASCADE,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (licence_id, computer_id)
);

CREATE INDEX IF NOT EXISTS ix_licence_assignments_licence_id ON licence_assignments (licence_id);
CREATE INDEX IF NOT EXISTS ix_licence_assignments_computer_id ON licence_assignments (computer_id);

-- ============================================================
-- ALERTS
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'warning',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    title VARCHAR(500) NOT NULL,
    message TEXT,
    metric_value FLOAT,
    threshold_value FLOAT,
    is_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alerts_computer_id ON alerts (computer_id);
CREATE INDEX IF NOT EXISTS ix_alerts_alert_type ON alerts (alert_type);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts (status);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts (created_at);
CREATE INDEX IF NOT EXISTS ix_alerts_computer_type_status ON alerts (computer_id, alert_type, status);

-- ============================================================
-- INCIDENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_number VARCHAR(30) UNIQUE NOT NULL,
    computer_id INTEGER REFERENCES computers(id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL DEFAULT 'other',
    severity VARCHAR(50) NOT NULL DEFAULT 'medium',
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    assigned_to_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_auto_created BOOLEAN NOT NULL DEFAULT FALSE,
    related_alert_id INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_incidents_computer_id ON incidents (computer_id);
CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS ix_incidents_severity ON incidents (severity);
CREATE INDEX IF NOT EXISTS ix_incidents_created_at ON incidents (created_at);
CREATE INDEX IF NOT EXISTS ix_incidents_assigned_to_id ON incidents (assigned_to_id);

-- ============================================================
-- INCIDENT UPDATES
-- ============================================================
CREATE TABLE IF NOT EXISTS incident_updates (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    update_type VARCHAR(50) NOT NULL DEFAULT 'comment',
    message TEXT NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_incident_updates_incident_id ON incident_updates (incident_id);
CREATE INDEX IF NOT EXISTS ix_incident_updates_created_at ON incident_updates (created_at);

-- ============================================================
-- MAINTENANCE RECORDS
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_records (
    id SERIAL PRIMARY KEY,
    computer_id INTEGER NOT NULL REFERENCES computers(id) ON DELETE CASCADE,
    performed_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    maintenance_type VARCHAR(50) NOT NULL DEFAULT 'preventive',
    title VARCHAR(500) NOT NULL,
    description TEXT,
    scheduled_date DATE,
    completed_date DATE,
    cost INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_maintenance_records_computer_id ON maintenance_records (computer_id);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_scheduled_date ON maintenance_records (scheduled_date);
CREATE INDEX IF NOT EXISTS ix_maintenance_records_completed_date ON maintenance_records (completed_date);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'info',
    related_id INTEGER,
    related_type VARCHAR(50),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read);
CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at);
CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications (user_id, is_read);

-- ============================================================
-- AUDIT LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_type ON audit_logs (entity_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);

-- ============================================================
-- SYSTEM SETTINGS
-- ============================================================
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    value_type VARCHAR(50) NOT NULL DEFAULT 'string',
    description TEXT,
    category VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_system_settings_key ON system_settings (key);
CREATE INDEX IF NOT EXISTS ix_system_settings_category ON system_settings (category);

-- ============================================================
-- DEFAULT SYSTEM SETTINGS
-- ============================================================
INSERT INTO system_settings (key, value, value_type, description, category) VALUES
    ('cpu_warning_percent', '90', 'float', 'CPU usage percentage threshold for warning alerts', 'thresholds'),
    ('ram_warning_percent', '90', 'float', 'RAM usage percentage threshold for warning alerts', 'thresholds'),
    ('disk_warning_percent', '90', 'float', 'Disk usage percentage threshold for warning alerts', 'thresholds'),
    ('disk_critical_percent', '95', 'float', 'Disk usage percentage threshold for critical alerts', 'thresholds'),
    ('offline_timeout_minutes', '10', 'integer', 'Minutes without heartbeat before computer is marked offline', 'monitoring'),
    ('heartbeat_interval_seconds', '60', 'integer', 'How often the monitoring agent sends a heartbeat', 'monitoring'),
    ('software_scan_interval_hours', '24', 'integer', 'How often the agent scans installed software', 'monitoring'),
    ('data_retention_days', '30', 'integer', 'Days of hardware/network metrics to retain', 'monitoring'),
    ('smtp_host', '', 'string', 'SMTP server hostname', 'smtp'),
    ('smtp_port', '587', 'integer', 'SMTP server port', 'smtp'),
    ('smtp_user', '', 'string', 'SMTP username/email', 'smtp'),
    ('smtp_password_encrypted', '', 'string', 'Fernet-encrypted SMTP password', 'smtp'),
    ('smtp_from', '', 'string', 'From address for outgoing emails', 'smtp')
ON CONFLICT (key) DO NOTHING;
