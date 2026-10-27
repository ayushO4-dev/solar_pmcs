# solar_pmcs

Solar Panel Monitoring & Control System: a dual-axis sun-tracking solar panel
on a Raspberry Pi 5, with a web dashboard for live readings and panel control.

## Layout

```
backend/            FastAPI service (Python, uv)
  app/
    main.py         app setup, background tasks, static frontend serving
    routers/        /api/sensor, /api/panel, /api/system + /api/config
    tracking.py     moves the panel's realtime angles towards the target angles
    sampler.py      samples sensors and stores readings in Postgres
    solar.py        optimal yaw/roll from the sun's position (pysolar)
    hardware/       stepper motor, LDR, INA219 and DHT11 drivers
    config.py       settings from environment / .env
  db/init/          Postgres schema, applied on first container start
frontend/           React + TypeScript + Tailwind dashboard (Vite)
cad/                Panel frame CAD files
docker-compose.yml  Postgres
```

## Running locally

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), Node.js 18+.

1. Configure and start Postgres:

   ```bash
   cp .env.example .env
   docker compose up -d db
   ```

2. Start the backend (port 8000, API docs at http://localhost:8000/docs):

   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

   With `SENSOR_MODE=simulated` (the default) the sampler stores random
   plausible readings, so the dashboard works without the Pi hardware.

3. Start the dashboard (http://localhost:5173; `/api` is proxied to the backend):

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Deploying on the Pi

Build the frontend once (`npm run build` in `frontend/`); the backend serves
`frontend/dist` at `/`, so only the backend port needs to be exposed. Install the
hardware drivers and read the real sensors with:

```bash
cd backend
uv sync --extra hardware
SENSOR_MODE=hardware uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Database

The schema in `backend/db/init/001_schema.sql` runs only when the Postgres data
volume is first created. After changing it, recreate the volume (this deletes
all stored data):

```bash
docker compose down -v
docker compose up -d db
```

## Panel model

- **yaw** (0–180°) and **roll** (35–145°) are the panel's two axes; the range
  is stored in `panel_state`.
- **expected** is the target set from the dashboard, by a schedule point or by
  sleep mode; **realtime** is where the panel is. The tracking loop steps
  realtime towards expected by 1° every 0.5 s.
- **curves** are a time-of-day schedule of yaw/roll points; *Load Optimal*
  fills it from the sun position for today.
- **offset** is the yaw/roll calibration between panel angles and motor angles.

The tracking loop currently simulates the movement; the stepper driver in
`app/hardware/motor.py` is not yet called by it.
