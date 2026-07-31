# Bestellsystem — Developer README

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite (port 5173) |
| Backend | Python 3.12 + Flask (port 5000) |
| Database | SQLite (`data/orders.db`) |
| Printer | EPSON TM-T20II via ESC/POS over TCP/IP |
| Deployment | Docker Compose + nginx |

---

## Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (for deployment)

---

## Local Development

### 1 — Backend (Flask)

```bash
cd flask_app

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run the dev server
python main.py
```

The API is now available at **http://localhost:5000**.

> **Tip:** To avoid needing a physical printer, set `MOCK_PRINTER = True` in
> [`flask_app/config.py`](./flask_app/config.py) before starting.

---

### 2 — Frontend (React / Vite)

The Vite dev server proxies API calls directly to your browser — it does **not** proxy to Flask automatically in dev mode. The frontend reads the API base URL from [`frontend/.env`](./frontend/.env):

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (http://localhost:5173)
npm run dev
```

Make sure `frontend/.env` points to your running Flask instance:

```env
# frontend/.env
VITE_API_URL=http://localhost:5000
```

> **Note:** In dev mode the frontend calls Flask directly (no nginx proxy).
> In production (Docker) nginx routes `/api/*` to the backend container.

---

### 3 — Printer Configuration

Edit [`flask_app/config.py`](./flask_app/config.py):

```python
MOCK_PRINTER    = False               # True = no real printer needed
FOOD_PRINTER_IP = "192.168.88.250"    # IP of food printer
DRINKS_PRINTER_IP = "192.168.88.248"  # IP of drinks/bar printer
```

---

## Docker Deployment

### Build & Start

```bash
# From the repository root
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (nginx) | http://\<host\>:80 |
| Backend (Flask) | http://\<host\>:5000 |

nginx proxies all `/api/*` requests to the Flask backend automatically.

### Stop

```bash
docker compose down
```

### Persistent Data

The SQLite database is stored in a named Docker volume (`flask_db_data`) and survives container restarts:

```bash
# Inspect the volume
docker volume inspect bestellsystem_flask_flask_db_data
```

### Printer Access from Docker

The printers must be reachable from the **host network**. By default Docker containers use a bridge network, so make sure:

1. The printer IPs are accessible from the host machine.
2. No firewall blocks TCP port `9100` (default ESC/POS port) from the container.

If needed, switch to host networking in `docker-compose.yml`:

```yaml
services:
  backend:
    network_mode: host   # direct access to host network
```

---

## Project Structure

```
Bestellsystem_flask/
├── docker-compose.yml
├── flask_app/
│   ├── main.py              # App entry point
│   ├── config.py            # All configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routes/              # Flask Blueprints
│   │   ├── order_routes.py
│   │   ├── menu_routes.py
│   │   └── analytics_routes.py
│   ├── services/
│   │   ├── order_service.py   # Order processing & queue
│   │   ├── printer_service.py # Printer management
│   │   ├── Printer.py         # ESC/POS network printer
│   │   ├── MockPrinter.py     # Mock for local dev
│   │   └── order_logger.py    # SQLite persistence
│   ├── resources/
│   │   └── menu.json
│   └── data/
│       └── orders.db          # SQLite database (gitignored)
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── .env                   # VITE_API_URL
    ├── package.json
    └── src/
        ├── App.jsx            # Menu page + routing
        ├── OrderSummary.jsx   # Order confirmation
        └── components/
            ├── Dashboard.jsx  # Kitchen display
            └── Summary.jsx    # Sales analytics
```

---

## Available Routes (Frontend)

| Path | View |
|---|---|
| `/` | Guest order menu |
| `/order-summary` | Order confirmation |
| `/dashboard` | Kitchen/bar display |
| `/summary` | Sales analytics |
