from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    order_id: int = Field(gt=0)
    payment_method: str = Field(
        pattern="^(UPI|CARD|COD)$"
    )


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    customer_id: int
    amount: Decimal
    payment_method: str
    transaction_id: str | None
    status: str
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(SUCCESS|FAILED|REFUNDED)$"
    )
