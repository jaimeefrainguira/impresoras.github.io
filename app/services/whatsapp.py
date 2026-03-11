import httpx

from app.core.config import get_settings

settings = get_settings()


class WhatsAppClient:
    def __init__(self):
        self.base_url = (
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/"
            f"{settings.whatsapp_phone_number_id}/messages"
        )
        self.graph_url = f"https://graph.facebook.com/{settings.whatsapp_api_version}"

    async def send_text(self, to: str, body: str) -> None:
        if not settings.whatsapp_token or not settings.whatsapp_phone_number_id:
            # Modo local/desarrollo: evita llamadas externas.
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

    async def download_media(self, media_id: str) -> tuple[bytes, str | None]:
        """Descarga binario de un media de WhatsApp Cloud API y retorna (bytes, mime_type)."""
        if not settings.whatsapp_token:
            # Fallback de desarrollo para permitir pruebas de flujo.
            return b"dev-placeholder", "application/octet-stream"

        headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            meta_resp = await client.get(f"{self.graph_url}/{media_id}", headers=headers)
            meta_resp.raise_for_status()
            meta = meta_resp.json()
            media_url = meta.get("url")
            mime_type = meta.get("mime_type")
            if not media_url:
                raise ValueError("No se recibió URL de descarga para el media_id")

            media_resp = await client.get(media_url, headers=headers)
            media_resp.raise_for_status()
            return media_resp.content, mime_type
