# How to run (simple)

Your Mac (macOS 12) cannot use the newest Docker Desktop. We use **Colima** instead.

## One-time setup (wait for install to finish if still running)

Open **Terminal** and run:

```bash
cd /Users/mac/Documents/projects/whatsapp
./setup-waha.sh
```

First run can take **30–60 minutes** (builds QEMU). Leave Terminal open until it says "Done".

## Every time you use the app

**Terminal 1 — WAHA** (if not already running):

```bash
colima start
cd /Users/mac/Documents/projects/whatsapp
docker compose up -d waha
```

**Terminal 2 — Web app:**

```bash
cd /Users/mac/Documents/projects/whatsapp
./start-app.sh
```

## Link WhatsApp (once)

1. Open http://localhost:3000/dashboard
2. API key: see `waha-env/.env` → `WAHA_API_KEY`
3. Username: `admin` / Password: see `WAHA_DASHBOARD_PASSWORD` in `waha-env/.env`
4. Start session **default** → scan QR with phone **+923034992699**

## Copy a group

1. Open http://localhost:8001
2. Source: `Crypto Drop` → New: `Crypto Earnings` → **Create new group and copy members**
