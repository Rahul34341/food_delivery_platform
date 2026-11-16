from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    delivery_address: str = Field(min_length=5, max_length=500)
    contact_phone: str = Field(min_length=10, max_length=20)


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    delivery_address: str
    contact_phone: str
    total_amount: Decimal
    status: str
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(CONFIRMED|PREPARING|READY_FOR_PICKUP|OUT_FOR_DELIVERY|DELIVERED|CANCELLED)$"
    )
