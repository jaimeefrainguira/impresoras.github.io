from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import Order, Payment, User
from app.models.enums import OrderStatus
from app.services.pricing import PricingService
from app.services.storage import save_bytes
from app.services.whatsapp import WhatsAppClient

settings = get_settings()

ALLOWED_SIZES = {"A4", "A3", "A2", "A1", "A0"}
ALLOWED_TYPES = {"COLOR": "color", "BLACK AND WHITE": "black_white", "BLACK_WHITE": "black_white"}
ALLOWED_MATERIALS = {"PAPEL BOND", "CARTULINA", "OTHER"}


class ConversationService:
    def __init__(self):
        self.whatsapp = WhatsAppClient()

    async def handle_document(
        self,
        db: Session,
        from_number: str,
        file_name: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> None:
        user = self._get_or_create_user(db, from_number)
        path = save_bytes(file_bytes, file_name)

        order = Order(
            user_id=user.id,
            file_name=file_name,
            file_path=path,
            file_mime=mime_type,
            status=OrderStatus.file_received,
            conversation_step="awaiting_size",
        )
        db.add(order)
        db.commit()

        await self.whatsapp.send_text(
            from_number,
            "¿Qué tamaño deseas imprimir?\nOpciones: A4, A3, A2, A1, A0",
        )

    async def handle_text(self, db: Session, from_number: str, text: str) -> None:
        order = self._get_active_order(db, from_number)
        if not order:
            await self.whatsapp.send_text(from_number, "Primero envía un archivo para iniciar tu pedido de impresión.")
            return

        clean_text = text.strip().upper()

        if order.conversation_step == "awaiting_size":
            if clean_text not in ALLOWED_SIZES:
                await self.whatsapp.send_text(from_number, "Tamaño inválido. Elige: A4, A3, A2, A1 o A0")
                return
            order.size = clean_text
            order.conversation_step = "awaiting_print_type"
            db.commit()
            await self.whatsapp.send_text(
                from_number,
                "¿Deseas impresión a color o blanco y negro?\nOpciones: Color, Black and White",
            )
            return

        if order.conversation_step == "awaiting_print_type":
            normalized = ALLOWED_TYPES.get(clean_text)
            if not normalized:
                await self.whatsapp.send_text(from_number, "Tipo inválido. Escribe: Color o Black and White.")
                return
            order.print_type = normalized
            order.conversation_step = "awaiting_material"
            db.commit()
            await self.whatsapp.send_text(
                from_number,
                "¿Sobre qué material deseas imprimir?\nOpciones: Papel Bond, Cartulina, Other",
            )
            return

        if order.conversation_step == "awaiting_material":
            if clean_text not in ALLOWED_MATERIALS:
                await self.whatsapp.send_text(from_number, "Material inválido. Elige: Papel Bond, Cartulina u Other.")
                return

            order.material = clean_text.title()
            order.status = OrderStatus.options_selected

            if clean_text != "PAPEL BOND":
                order.requires_human = True
                order.conversation_step = "waiting_human"
                db.commit()
                await self.whatsapp.send_text(
                    from_number,
                    "Un operador te asistirá para coordinar este material.",
                )
                await self._notify_admin(
                    f"⚠️ Pedido #{order.id} requiere atención humana. Material solicitado: {order.material}."
                )
                return

            order.total_price = PricingService.calculate_total(db, order)
            order.status = OrderStatus.payment_pending
            order.conversation_step = "awaiting_payment_receipt"
            db.commit()
            await self.whatsapp.send_text(from_number, self._summary_message(order))
            return

        if order.conversation_step == "awaiting_payment_receipt":
            await self.whatsapp.send_text(from_number, "Por favor envía la imagen o PDF del comprobante de pago.")
            return

    async def handle_payment_receipt(
        self,
        db: Session,
        from_number: str,
        file_name: str,
        file_bytes: bytes,
    ) -> None:
        order = self._get_active_order(db, from_number)
        if not order:
            await self.whatsapp.send_text(from_number, "No encontramos un pedido activo. Envía un archivo para comenzar.")
            return

        path = save_bytes(file_bytes, file_name)
        payment = Payment(order_id=order.id, receipt_path=path, status="pending_review")
        order.status = OrderStatus.payment_review
        order.conversation_step = "payment_in_review"
        db.add(payment)
        db.commit()

        await self.whatsapp.send_text(from_number, "Comprobante recibido. Nuestro equipo lo validará en breve.")
        await self._notify_admin(f"💳 Pedido #{order.id} recibió comprobante y está en revisión de pago.")

    def _get_or_create_user(self, db: Session, from_number: str) -> User:
        user = db.query(User).filter(User.whatsapp_number == from_number).first()
        if user:
            return user
        user = User(whatsapp_number=from_number)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def _get_active_order(self, db: Session, from_number: str) -> Order | None:
        return (
            db.query(Order)
            .join(User, User.id == Order.user_id)
            .filter(User.whatsapp_number == from_number)
            .filter(
                Order.status.in_(
                    [
                        OrderStatus.file_received,
                        OrderStatus.options_selected,
                        OrderStatus.payment_pending,
                        OrderStatus.payment_review,
                    ]
                )
            )
            .order_by(Order.created_at.desc())
            .first()
        )

    async def _notify_admin(self, message: str) -> None:
        if settings.admin_notify_phone:
            await self.whatsapp.send_text(settings.admin_notify_phone, message)

    def _summary_message(self, order: Order) -> str:
        type_label = "Color" if order.print_type == "color" else "Blanco y Negro"
        return (
            "📄 Resumen de impresión\n\n"
            f"Tamaño: {order.size}\n"
            f"Tipo: {type_label}\n"
            f"Material: {order.material}\n"
            f"Páginas: {order.pages}\n\n"
            f"Total: ${order.total_price}\n\n"
            "Métodos de pago:\n- DeUna\n- Transferencia Bancaria\n\n"
            "Por favor envía aquí tu comprobante de pago."
        )
