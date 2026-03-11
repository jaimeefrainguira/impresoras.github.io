from sqlalchemy.orm import Session

from app.models.entities import Order, PrintPrice


class PricingService:
    @staticmethod
    def calculate_total(db: Session, order: Order) -> float:
        price = (
            db.query(PrintPrice)
            .filter(
                PrintPrice.size == order.size,
                PrintPrice.print_type == order.print_type,
                PrintPrice.material == order.material,
            )
            .first()
        )
        if not price:
            raise ValueError("Price configuration missing for selected options")

        if order.print_type == "color":
            return round(price.base_price + (price.price_color * order.pages), 2)
        return round(price.base_price + (price.price_bw * order.pages), 2)
