from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import OrderStatus


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    whatsapp_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    orders: Mapped[list["Order"]] = relationship(back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.file_received)

    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_mime: Mapped[str | None] = mapped_column(String(100), nullable=True)

    size: Mapped[str | None] = mapped_column(String(10), nullable=True)
    print_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    material: Mapped[str | None] = mapped_column(String(50), nullable=True)

    pages: Mapped[int] = mapped_column(Integer, default=1)
    color_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    conversation_step: Mapped[str] = mapped_column(String(50), default="awaiting_size")
    requires_human: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="orders")
    payments: Mapped[list["Payment"]] = relationship(back_populates="order")


class PrintPrice(Base):
    __tablename__ = "print_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    size: Mapped[str] = mapped_column(String(10), nullable=False)
    print_type: Mapped[str] = mapped_column(String(20), nullable=False)
    material: Mapped[str] = mapped_column(String(50), nullable=False)
    price_color: Mapped[float] = mapped_column(Float, nullable=False)
    price_bw: Mapped[float] = mapped_column(Float, nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    receipt_path: Mapped[str] = mapped_column(Text, nullable=False)
    amount_reported: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order: Mapped[Order] = relationship(back_populates="payments")
