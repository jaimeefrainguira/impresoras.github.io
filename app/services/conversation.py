from sqlalchemy.orm import Session

from app.models.entities import Order, Payment, User
from app.models.enums import OrderStatus
from app.services.pricing import PricingService
from app.services.storage import save_bytes
from app.services.whatsapp import WhatsAppClient

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
            "What size do you want to print?\nOptions: A4, A3, A2, A1, A0",
        )

    async def handle_text(self, db: Session, from_number: str, text: str) -> None:
        order = self._get_active_order(db, from_number)
        if not order:
            await self.whatsapp.send_text(from_number, "Please send a file to start your print order.")
            return

        clean_text = text.strip().upper()

        if order.conversation_step == "awaiting_size":
            if clean_text not in ALLOWED_SIZES:
                await self.whatsapp.send_text(from_number, "Invalid size. Please choose one of: A4, A3, A2, A1, A0")
                return
            order.size = clean_text
            order.conversation_step = "awaiting_print_type"
            db.commit()
            await self.whatsapp.send_text(
                from_number,
                "Do you want the print in color or black and white?\nOptions: Color, Black and White",
            )
            return

        if order.conversation_step == "awaiting_print_type":
            normalized = ALLOWED_TYPES.get(clean_text)
            if not normalized:
                await self.whatsapp.send_text(from_number, "Invalid type. Choose Color or Black and White.")
                return
            order.print_type = normalized
            order.conversation_step = "awaiting_material"
            db.commit()
            await self.whatsapp.send_text(
                from_number,
                "What material do you want to print on?\nOptions: Papel Bond, Cartulina, Other",
            )
            return

        if order.conversation_step == "awaiting_material":
            if clean_text not in ALLOWED_MATERIALS:
                await self.whatsapp.send_text(from_number, "Invalid material. Choose Papel Bond, Cartulina, or Other.")
                return

            order.material = clean_text.title()
            order.status = OrderStatus.options_selected

            if clean_text != "PAPEL BOND":
                order.requires_human = True
                order.conversation_step = "waiting_human"
                db.commit()
                await self.whatsapp.send_text(
                    from_number,
                    "An operator will assist you to coordinate this material.",
                )
                return

            order.total_price = PricingService.calculate_total(db, order)
            order.status = OrderStatus.payment_pending
            order.conversation_step = "awaiting_payment_receipt"
            db.commit()
            await self.whatsapp.send_text(from_number, self._summary_message(order))
            return

        if order.conversation_step == "awaiting_payment_receipt":
            await self.whatsapp.send_text(from_number, "Please send your payment receipt image or PDF.")
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
            await self.whatsapp.send_text(from_number, "No active order found. Send a file to begin.")
            return

        path = save_bytes(file_bytes, file_name)
        payment = Payment(order_id=order.id, receipt_path=path, status="pending_review")
        order.status = OrderStatus.payment_review
        order.conversation_step = "payment_in_review"
        db.add(payment)
        db.commit()

        await self.whatsapp.send_text(from_number, "Payment receipt received. Our team will verify it shortly.")

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

    def _summary_message(self, order: Order) -> str:
        return (
            "📄 Print Order Summary\n\n"
            f"Size: {order.size}\n"
            f"Type: {order.print_type}\n"
            f"Material: {order.material}\n"
            f"Pages: {order.pages}\n\n"
            f"Total price: ${order.total_price}\n\n"
            "Payment methods:\n- DeUna\n- Bank Transfer\n\n"
            "Please send the payment receipt here."
        )
