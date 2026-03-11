import httpx
from app.core.config import get_settings

settings = get_settings()


class WhatsAppClient:
    def __init__(self):
        self.base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )

    async def send_text(self, to: str, body: str) -> None:
        if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
            # local/dev mode - skip external call
            return

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
