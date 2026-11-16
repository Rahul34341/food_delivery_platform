from pydantic import BaseModel, ConfigDict, Field


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    address: str = Field(min_length=5, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    address: str | None = Field(default=None, min_length=5, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)


class RestaurantResponse(BaseModel):
    id: int
    name: str
    description: str | None
    address: str
    city: str
    phone: str | None
    logo_url: str | None
    banner_url: str | None
    owner_id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
