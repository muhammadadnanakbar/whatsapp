# WhatsApp Group Copier (WAHA)

Web UI to create a new WhatsApp group and copy all members from an existing group you belong to, using [WAHA](https://waha.devlike.pro/).

## Prerequisites

1. **WAHA** running and connected to your WhatsApp (`+923034992699` or any number).
2. **Python 3.11+** (for local run).

## Quick start

### 1. Start WAHA

```bash
docker compose up -d waha
```

Open http://localhost:3000 — create session `default`, scan QR with WhatsApp on your phone.

### 2. Configure

```bash
cp .env.example .env
# Edit .env if WAHA uses an API key or different URL
```

### 3. Run the app

```bash
pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

Open http://localhost:8001

### 4. Copy a group

1. **Source group name**: e.g. `Crypto Drop` (or pick from the list).
2. **New group name**: e.g. `Crypto Earnings`.
3. Click **Create new group and copy members**.

You will be admin of the new group. WhatsApp may not add every member (privacy, contacts, rate limits).

## API

- `GET /api/health` — WAHA connection
- `GET /api/groups?q=` — list/search groups
- `POST /api/groups/copy` — body: `{ "source_group_name", "new_group_name", "source_group_id?" }`

## Notes

- You must be a member of the source group.
- Large groups are added in batches (see `PARTICIPANT_BATCH_SIZE` in `.env`).
- Duplicate group names: the UI asks you to pick the correct one.
