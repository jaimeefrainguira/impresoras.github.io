from enum import Enum


class OrderStatus(str, Enum):
    file_received = "file_received"
    options_selected = "options_selected"
    price_sent = "price_sent"
    payment_pending = "payment_pending"
    payment_review = "payment_review"
    approved_for_print = "approved_for_print"
    printing = "printing"
    ready_for_pickup = "ready_for_pickup"


class PrintType(str, Enum):
    color = "color"
    black_white = "black_white"
