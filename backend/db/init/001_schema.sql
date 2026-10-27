-- Solar Panel Monitoring & Control schema.
-- Mounted into the postgres container's docker-entrypoint-initdb.d, so it runs
-- only when the data volume is first created.

-- Time series from the INA219 (voltage/current/wattage) and DHT11 (temperature/humidity).
-- Values are stored with sensor offsets already applied.
CREATE TABLE sensor_readings (
  id          bigserial PRIMARY KEY,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  voltage     double precision,
  current     double precision,
  wattage     double precision,
  temperature double precision,
  humidity    double precision
);
CREATE INDEX sensor_readings_recorded_at_idx ON sensor_readings (recorded_at DESC);

-- Calibration offsets added to raw sensor values before they are stored.
CREATE TABLE sensor_offsets (
  sensor     text PRIMARY KEY
             CHECK (sensor IN ('voltage', 'current', 'wattage', 'temperature', 'humidity')),
  value      double precision NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO sensor_offsets (sensor) VALUES
  ('voltage'), ('current'), ('wattage'), ('temperature'), ('humidity');

-- Single-row panel state. The tracking loop steps "realtime" towards "expected"
-- one increment at a time, clamped to the yaw/roll range.
CREATE TABLE panel_state (
  id            smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  realtime_yaw  double precision NOT NULL DEFAULT 90,
  realtime_roll double precision NOT NULL DEFAULT 90,
  expected_yaw  double precision NOT NULL DEFAULT 90,
  expected_roll double precision NOT NULL DEFAULT 90,
  yaw_min       double precision NOT NULL DEFAULT 0,
  yaw_max       double precision NOT NULL DEFAULT 180,
  roll_min      double precision NOT NULL DEFAULT 35,
  roll_max      double precision NOT NULL DEFAULT 145,
  offset_yaw    double precision NOT NULL DEFAULT 0,
  offset_roll   double precision NOT NULL DEFAULT 0,
  updated_at    timestamptz NOT NULL DEFAULT now()
);
INSERT INTO panel_state DEFAULT VALUES;

-- Time-of-day schedule of target angles.
CREATE TABLE angle_curves (
  slot_time time PRIMARY KEY,
  yaw       double precision NOT NULL,
  roll      double precision NOT NULL
);

-- Single-row operational status set from the dashboard (active, sleep, reboot, shutdown).
CREATE TABLE system_state (
  id               smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  status           text NOT NULL DEFAULT 'active',
  firmware_version text NOT NULL DEFAULT '1.0.0',
  updated_at       timestamptz NOT NULL DEFAULT now()
);
INSERT INTO system_state DEFAULT VALUES;

-- Free-form key/value settings.
CREATE TABLE system_config (
  key        text PRIMARY KEY,
  value      text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO system_config (key, value) VALUES ('api_server', 'http://localhost:8000');
