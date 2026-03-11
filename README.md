# WhatsApp Printing Order System

Production-ready starter implementation for automated print ordering through WhatsApp Business Cloud API.

## 1) Full Backend Project Structure

```text
app/
  api/
    admin.py
    orders.py
    webhook.py
  core/
    config.py
  db/
    session.py
  models/
    entities.py
    enums.py
  schemas/
    order.py
  services/
    conversation.py
    pricing.py
    storage.py
    whatsapp.py
  static/
    styles.css
  templates/
    dashboard.html
  storage/
sql/
  schema.sql
.env.example
requirements.txt
```

## 2) Database Schema
- PostgreSQL schema is in `sql/schema.sql` and includes `users`, `orders`, `print_prices`, and `payments`.

## 3) WhatsApp Webhook Code
- `app/api/webhook.py` handles verification (`GET`) and message events (`POST`).
- Supports text + document/image message flows.

## 4) Conversation Flow Logic
- `app/services/conversation.py` provides state-machine behavior:
  - file received -> ask size
  - ask print type
  - ask material
  - if not Papel Bond -> handoff to human
  - else calculate price and request payment receipt
  - payment receipt -> payment review

## 5) Price Calculation Service
- `app/services/pricing.py` reads `print_prices` and applies formulas:
  - color: `base_price + price_color * pages`
  - black/white: `base_price + price_bw * pages`

## 6) Admin Dashboard Basic UI
- `/admin/orders` renders `app/templates/dashboard.html`.
- Allows approving payment and moving status to printing / ready_for_pickup.

## 7) API Endpoints
- `GET /health`
- `GET /webhooks/whatsapp` (verify callback)
- `POST /webhooks/whatsapp` (incoming WhatsApp events)
- `GET /api/orders` (JSON order list)
- `GET /admin/orders` (dashboard)
- `POST /admin/orders/{id}/approve`
- `POST /admin/orders/{id}/status`

## 8) Example Configuration
- `.env.example` includes app, DB, storage, and WhatsApp variables.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open dashboard at `http://localhost:8000/admin/orders`.
