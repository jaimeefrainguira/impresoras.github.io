from datetime import datetime
from pydantic import BaseModel


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    file_name: str
    size: str | None
    print_type: str | None
    material: str | None
    pages: int
    total_price: float | None
    requires_human: bool
    created_at: datetime

    class Config:
        from_attributes = True
