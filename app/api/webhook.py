from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.conversation import ConversationService

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
settings = get_settings()
service = ConversationService()


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


@router.post("")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
    except (KeyError, IndexError, TypeError):
        return {"status": "ignored"}

    for message in messages:
        from_number = message.get("from")
        message_type = message.get("type")
        if not from_number or not message_type:
            continue

        if message_type == "text":
            text = message["text"].get("body", "")
            await service.handle_text(db, from_number, text)

        elif message_type in {"document", "image"}:
            media_data = message.get(message_type, {})
            media_id = media_data.get("id")
            file_name = media_data.get("filename", f"{message_type}.bin")

            try:
                if media_id:
                    file_bytes, mime_type = await service.whatsapp.download_media(media_id)
                else:
                    file_bytes, mime_type = b"dev-placeholder", media_data.get("mime_type", "application/octet-stream")
            except Exception:
                await service.whatsapp.send_text(
                    from_number,
                    "No pudimos descargar tu archivo en este momento. Por favor reinténtalo en unos minutos.",
                )
                continue

            mime_type = mime_type or media_data.get("mime_type", "application/octet-stream")
            active_order = service._get_active_order(db, from_number)
            if active_order and active_order.conversation_step == "awaiting_payment_receipt":
                await service.handle_payment_receipt(db, from_number, file_name, file_bytes)
            else:
                await service.handle_document(db, from_number, file_name, mime_type, file_bytes)

    return {"status": "ok"}
