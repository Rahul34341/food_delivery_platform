from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeliveryAssign(BaseModel):
    order_id: int = Field(gt=0)
    delivery_partner_id: int = Field(gt=0)


class DeliveryStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(ACCEPTED|REJECTED|PICKED_UP|OUT_FOR_DELIVERY|DELIVERED)$"
    )


class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    delivery_partner_id: int
    status: str
    picked_up_at: datetime | None
    delivered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
