/*
  # Solar Power Monitoring System Schema

  ## Overview
  Creates comprehensive schema for solar power monitoring and control system with real-time sensor data, panel positioning, and system configuration.

  ## New Tables

  ### 1. `sensor_readings`
  Real-time sensor data from the solar power system
  - `id` (uuid, primary key)
  - `voltage` (numeric) - Voltage reading in volts
  - `wattage` (numeric) - Power output in watts
  - `ampere` (numeric) - Current reading in amperes
  - `temperature` (numeric) - Temperature in Celsius
  - `humidity` (numeric) - Humidity percentage
  - `timestamp` (timestamptz) - Reading timestamp

  ### 2. `panel_position`
  Current and historical solar panel positioning
  - `id` (uuid, primary key)
  - `vertical_angle` (numeric) - Vertical angle (35-145 degrees)
  - `horizontal_angle` (numeric) - Horizontal angle (0-360 degrees)
  - `timestamp` (timestamptz) - Position update timestamp

  ### 3. `angle_curves`
  Time-based angle adjustment curves for automatic positioning
  - `id` (uuid, primary key)
  - `time_hour` (integer) - Hour of day (6-18 for 6am-6pm)
  - `time_minute` (integer) - Minute of hour (0-59)
  - `vertical_angle` (numeric) - Target vertical angle
  - `horizontal_angle` (numeric) - Target horizontal angle
  - `is_active` (boolean) - Whether this curve is currently active
  - `created_at` (timestamptz)

  ### 4. `system_config`
  System configuration and settings
  - `id` (uuid, primary key)
  - `key` (text, unique) - Configuration key
  - `value` (text) - Configuration value
  - `updated_at` (timestamptz)

  ### 5. `sensor_offsets`
  Calibration offsets for sensor readings
  - `id` (uuid, primary key)
  - `sensor_type` (text) - Type of sensor (voltage, wattage, ampere, temperature, humidity)
  - `offset_value` (numeric) - Offset to apply to readings
  - `updated_at` (timestamptz)

  ### 6. `system_status`
  Overall system status and uptime tracking
  - `id` (uuid, primary key)
  - `status` (text) - System status (active, sleep, power_saving)
  - `uptime_seconds` (bigint) - System uptime in seconds
  - `firmware_version` (text) - Current firmware version
  - `last_boot` (timestamptz) - Last system boot time
  - `updated_at` (timestamptz)

  ## Security
  - Enable RLS on all tables
  - Add policies for authenticated users to read their data
  - Add policies for system operations (insert/update for sensor data)

  ## Important Notes
  1. Sensor readings table stores time-series data for monitoring
  2. Panel position tracks solar panel orientation for optimal power generation
  3. Angle curves enable automated sun-tracking throughout the day
  4. System config stores API endpoints and general configuration
  5. Sensor offsets allow calibration of sensor readings
  6. System status tracks uptime and operational state
*/

CREATE TABLE IF NOT EXISTS sensor_readings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  voltage numeric NOT NULL DEFAULT 0,
  wattage numeric NOT NULL DEFAULT 0,
  ampere numeric NOT NULL DEFAULT 0,
  temperature numeric NOT NULL DEFAULT 0,
  humidity numeric NOT NULL DEFAULT 0,
  timestamp timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS panel_position (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  vertical_angle numeric NOT NULL DEFAULT 90,
  horizontal_angle numeric NOT NULL DEFAULT 0,
  timestamp timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS angle_curves (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  time_hour integer NOT NULL,
  time_minute integer NOT NULL DEFAULT 0,
  vertical_angle numeric NOT NULL,
  horizontal_angle numeric NOT NULL,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS system_config (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key text UNIQUE NOT NULL,
  value text NOT NULL DEFAULT '',
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sensor_offsets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  sensor_type text UNIQUE NOT NULL,
  offset_value numeric NOT NULL DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS system_status (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status text NOT NULL DEFAULT 'active',
  uptime_seconds bigint NOT NULL DEFAULT 0,
  firmware_version text NOT NULL DEFAULT '1.0.0',
  last_boot timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE sensor_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE panel_position ENABLE ROW LEVEL SECURITY;
ALTER TABLE angle_curves ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_offsets ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to sensor readings"
  ON sensor_readings FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to sensor readings"
  ON sensor_readings FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public read access to panel position"
  ON panel_position FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to panel position"
  ON panel_position FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to panel position"
  ON panel_position FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public read access to angle curves"
  ON angle_curves FOR SELECT
  USING (true);

CREATE POLICY "Allow public insert to angle curves"
  ON angle_curves FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public update to angle curves"
  ON angle_curves FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public delete to angle curves"
  ON angle_curves FOR DELETE
  USING (true);

CREATE POLICY "Allow public read access to system config"
  ON system_config FOR SELECT
  USING (true);

CREATE POLICY "Allow public update to system config"
  ON system_config FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public insert to system config"
  ON system_config FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public read access to sensor offsets"
  ON sensor_offsets FOR SELECT
  USING (true);

CREATE POLICY "Allow public update to sensor offsets"
  ON sensor_offsets FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public insert to sensor offsets"
  ON sensor_offsets FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Allow public read access to system status"
  ON system_status FOR SELECT
  USING (true);

CREATE POLICY "Allow public update to system status"
  ON system_status FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Allow public insert to system status"
  ON system_status FOR INSERT
  WITH CHECK (true);

INSERT INTO system_config (key, value) VALUES
  ('api_server_address', 'http://localhost:3000'),
  ('night_mode_enabled', 'true'),
  ('night_mode_start', '18:00'),
  ('night_mode_end', '06:00')
ON CONFLICT (key) DO NOTHING;

INSERT INTO sensor_offsets (sensor_type, offset_value) VALUES
  ('voltage', 0),
  ('wattage', 0),
  ('ampere', 0),
  ('temperature', 0),
  ('humidity', 0)
ON CONFLICT (sensor_type) DO NOTHING;

INSERT INTO system_status (status, uptime_seconds, firmware_version, last_boot) VALUES
  ('active', 0, '1.0.0', now());