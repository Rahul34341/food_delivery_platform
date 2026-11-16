from decimal import Decimal

from pydantic import BaseModel, Field


# Add item to cart
class CartItemCreate(BaseModel):
    menu_item_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


# Update cart item quantity
class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


# Individual cart item response
class CartItemResponse(BaseModel):
    id: int
    menu_item_id: int
    item_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


# Complete cart response
class CartResponse(BaseModel):
    id: int
    user_id: int
    restaurant_id: int | None
    items: list[CartItemResponse]
    total_amount: Decimal
