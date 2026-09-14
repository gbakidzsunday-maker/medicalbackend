# MedMon Backend

A FastAPI backend built to match your ESP32 firmware's HTTP calls exactly,
plus a small live dashboard for visualization.

## How it lines up with the firmware

| Firmware call | Backend route |
|---|---|
| `POST {backendUrl}/api/auth/login` with `{username, password}` | `POST /api/auth/login` → `{access_token}` |
| `POST {backendUrl}/api/readings` with `Authorization: Bearer <jwt>` | `POST /api/readings` (JWT required) |

The `ReadingIn` schema (`app/schemas.py`) has the same field names as the
JSON your `sendToBackend()` function builds (`device_name`, `temp_C`,
`temp_valid`, `spo2`, `finger_on_sensor`, `bpm_avg`, `bpm_valid`, `raw_red`,
`raw_ir`, `wifi_rssi`, `device_timestamp_ms`) — no firmware changes needed
beyond pointing `backend_url` at your deployed service (via the captive
portal, or by changing `DEFAULT_BACKEND_URL`).

## Endpoints

- `POST /api/auth/login` — device/dashboard login, returns a JWT
- `POST /api/readings` — device posts one reading (JWT required)
- `GET /api/readings?device_name=...&limit=100` — history for charts
- `GET /api/readings/latest?device_name=...` — most recent reading
- `GET /api/devices` — devices seen so far, for a device picker
- `WS /ws/live` — pushes `{"type": "reading", "data": {...}}` the instant a
  new reading is POSTed, so the dashboard updates without polling
- `GET /dashboard` — the bundled visualization page
- `GET /docs` — interactive Swagger UI

## Running locally

```bash
cp .env.example .env      # edit ADMIN_PASSWORD / JWT_SECRET_KEY at minimum
docker compose up --build
```

Then open `http://localhost:8000/dashboard`, and point your ESP32's
`backend_url` (via the `MedMon-Setup` captive portal) at
`http://<your-machine-ip>:8000`.

## Deploying to Render

1. Push this folder to a GitHub repo.
2. In Render: **New → Blueprint**, point it at the repo — `render.yaml`
   provisions the web service and a free Postgres database automatically.
3. Set `ADMIN_USERNAME` / `ADMIN_PASSWORD` in the Render dashboard
   (they're marked `sync: false` in `render.yaml` so Render will prompt for
   them rather than committing them to git). `JWT_SECRET_KEY` is
   auto-generated.
4. Once deployed, your API is at `https://<service>.onrender.com` and the
   dashboard at `https://<service>.onrender.com/dashboard`.
5. In the ESP32 captive portal, set the Backend API URL field to
   `https://<service>.onrender.com` (no trailing slash — the firmware
   appends `/api/readings` itself).

No `render.yaml`? You can also just create a Web Service manually, pick
"Docker" as the environment, and add a Postgres instance + the same env
vars by hand.

## Security notes (please read before this touches real patients)

- The firmware currently hardcodes `admin` / `admin123` for device login.
  Change `ADMIN_PASSWORD` on the backend **and** update the firmware's
  `authenticateWithBackend()` credentials to match — don't ship the
  default password.
- `GET /api/readings` and `/api/devices` are open by default (no auth) so
  the dashboard is easy to load. If this will ever hold real health data,
  put them behind the same `require_auth` dependency used on `POST
  /api/readings` and have the dashboard log in too.
- The firmware itself notes the SpO2 formula is a generic linear
  approximation, not a per-device clinical calibration — worth surfacing
  that caveat on the dashboard too if anyone besides you will read it.
- Free-tier Render web services spin down when idle; the first request
  after idle can take 30–60s, and free Postgres instances expire after 90
  days. Fine for a prototype, not for anything that needs to be always-on.

## Project layout

```
app/
  main.py          FastAPI app, CORS, static dashboard mount
  config.py        env-var settings
  database.py      SQLAlchemy engine/session
  models.py        Device, Reading tables
  schemas.py       Pydantic request/response models
  security.py      JWT + credential check
  ws_manager.py    WebSocket broadcast to connected dashboards
  routers/
    auth.py        /api/auth/login
    readings.py    /api/readings (POST + GET), /api/readings/latest
    devices.py     /api/devices
    ws.py          /ws/live
frontend/
  index.html       live dashboard (Chart.js + WebSocket)
Dockerfile
docker-compose.yml
render.yaml
.env.example
```
