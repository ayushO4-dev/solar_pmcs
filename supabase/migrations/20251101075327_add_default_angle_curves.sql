/*
  # Add Default Flat Angle Curves

  Inserts default angle curves for flat panel positioning throughout the day.
  This creates a baseline curve from 6 AM to 6 PM with consistent angles.
*/

INSERT INTO angle_curves (time_hour, time_minute, vertical_angle, horizontal_angle, is_active) VALUES
  (6, 0, 90, 0, true),
  (8, 0, 70, 60, true),
  (10, 0, 60, 90, true),
  (12, 0, 50, 120, true),
  (14, 0, 60, 150, true),
  (16, 0, 70, 180, true),
  (18, 0, 90, 0, true)
ON CONFLICT DO NOTHING;