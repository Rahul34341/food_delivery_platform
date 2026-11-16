from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# -------------------------
# Menu Category Schemas
# -------------------------

class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None


class MenuCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class MenuCategoryResponse(BaseModel):
    id: int
    restaurant_id: int
    name: str
    description: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Menu Item Schemas
# -------------------------

class MenuItemCreate(BaseModel):
    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    image_url: str | None = Field(default=None, max_length=500)
    is_vegetarian: bool = False
    preparation_time_minutes: int = Field(default=20, gt=0)


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    image_url: str | None = Field(default=None, max_length=500)
    is_vegetarian: bool | None = None
    is_available: bool | None = None
    preparation_time_minutes: int | None = Field(default=None, gt=0)


class MenuItemResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    image_url: str | None
    is_vegetarian: bool
    is_available: bool
    preparation_time_minutes: int

    model_config = ConfigDict(from_attributes=True)
