from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Order
from app.models.enums import OrderStatus
from app.services.whatsapp import WhatsAppClient

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")
wa = WhatsAppClient()


@router.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request, db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "orders": orders})


@router.post("/orders/{order_id}/approve")
async def approve_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/admin/orders", status_code=303)

    order.status = OrderStatus.approved_for_print
    db.commit()
    await wa.send_text(order.user.whatsapp_number, "✅ Pago verificado. Tu pedido fue aprobado para impresión.")
    return RedirectResponse(url="/admin/orders", status_code=303)


@router.post("/orders/{order_id}/status")
async def update_status(order_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/admin/orders", status_code=303)

    order.status = OrderStatus(status)
    db.commit()

    notifications = {
        OrderStatus.printing: "🖨️ Tu pedido ingresó a proceso de impresión.",
        OrderStatus.ready_for_pickup: "📦 Tu impresión está lista para retiro.",
    }
    note = notifications.get(order.status)
    if note:
        await wa.send_text(order.user.whatsapp_number, note)

    return RedirectResponse(url="/admin/orders", status_code=303)
