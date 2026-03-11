# Sistema de Pedidos de Impresión por WhatsApp

Implementación base orientada a producción para automatizar pedidos de impresión usando WhatsApp Business Cloud API.

## 1) Estructura completa del backend

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

## 2) Esquema de base de datos
- El esquema PostgreSQL está en `sql/schema.sql` e incluye las tablas `users`, `orders`, `print_prices` y `payments`.

## 3) Código de webhook de WhatsApp
- `app/api/webhook.py` maneja verificación (`GET`) y eventos entrantes (`POST`).
- Soporta mensajes de texto y documentos/imágenes.
- Descarga archivos reales usando el `media_id` de WhatsApp Cloud API.

## 4) Lógica de flujo conversacional
- `app/services/conversation.py` implementa la máquina de estados:
  - archivo recibido -> pedir tamaño
  - pedir tipo de impresión
  - pedir material
  - si no es Papel Bond -> derivar a operador
  - si es Papel Bond -> calcular precio y solicitar comprobante
  - comprobante recibido -> estado de revisión de pago

## 5) Servicio de cálculo de precios
- `app/services/pricing.py` consulta `print_prices` y aplica:
  - color: `base_price + price_color * pages`
  - blanco/negro: `base_price + price_bw * pages`

## 6) Panel administrativo básico
- `/admin/orders` renderiza `app/templates/dashboard.html`.
- Permite aprobar pagos y mover estados a `printing` / `ready_for_pickup`.

## 7) Endpoints API
- `GET /health`
- `GET /webhooks/whatsapp` (verificación)
- `POST /webhooks/whatsapp` (eventos entrantes)
- `GET /api/orders` (listado JSON)
- `GET /admin/orders` (panel)
- `POST /admin/orders/{id}/approve`
- `POST /admin/orders/{id}/status`

## 8) Configuración de ejemplo
- `.env.example` contiene variables de app, base de datos, almacenamiento y WhatsApp.

## Ejecutar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Abre el panel en `http://localhost:8000/admin/orders`.
