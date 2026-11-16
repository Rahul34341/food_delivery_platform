from pathlib import Path
from uuid import uuid4
from io import BytesIO

from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File
)
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models import Restaurant, User
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
)

router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"],
)

UPLOAD_DIR = Path("uploads") / "restaurants"
MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def get_owned_restaurant(
    restaurant_id: int,
    current_user: User,
    db: Session,
):
    restaurant = db.get(Restaurant, restaurant_id)

    if restaurant is None or restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return restaurant


async def save_restaurant_image(
    file: UploadFile,
    image_type: str,
    restaurant_id: int,
):
    contents = await file.read(MAX_IMAGE_SIZE + 1)
    await file.close()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select an image",
        )

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image size must not exceed 5 MB",
        )

    try:
        image = Image.open(BytesIO(contents))
        image.verify()

        if image.format not in ALLOWED_IMAGE_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG and WEBP images are allowed",
            )

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file",
        )

    extension = ALLOWED_IMAGE_FORMATS[image.format]

    folder = UPLOAD_DIR / image_type
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"{restaurant_id}_{uuid4().hex}{extension}"
    file_path = folder / filename

    file_path.write_bytes(contents)

    return f"/uploads/restaurants/{image_type}/{filename}"


# Create a restaurant - Restaurant Owner only
@router.post(
    "/",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = Restaurant(
        **restaurant_data.model_dump(),
        owner_id=current_user.id,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


# List all active restaurants - Public
@router.get("/", response_model=list[RestaurantResponse])
def get_restaurants(
    db: Session = Depends(get_db),
):
    restaurants = db.scalars(
        select(Restaurant).where(Restaurant.is_active.is_(True))
    ).all()

    return restaurants


# List restaurants belonging to logged-in owner
@router.get("/my-restaurants", response_model=list[RestaurantResponse])
def get_my_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurants = db.scalars(
        select(Restaurant).where(
            Restaurant.owner_id == current_user.id
        )
    ).all()

    return restaurants


# Upload restaurant logo - Owner only
@router.post("/{restaurant_id}/logo", response_model=RestaurantResponse)
async def upload_restaurant_logo(
    restaurant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    image_url = await save_restaurant_image(
        file, "logos", restaurant_id
    )

    restaurant.logo_url = image_url

    db.commit()
    db.refresh(restaurant)

    return restaurant


# Upload restaurant banner - Owner only
@router.post("/{restaurant_id}/banner", response_model=RestaurantResponse)
async def upload_restaurant_banner(
    restaurant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    image_url = await save_restaurant_image(
        file, "banners", restaurant_id
    )

    restaurant.banner_url = image_url

    db.commit()
    db.refresh(restaurant)

    return restaurant


# Enable restaurant - Owner only
@router.patch("/{restaurant_id}/enable", response_model=RestaurantResponse)
def enable_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    restaurant.is_active = True

    db.commit()
    db.refresh(restaurant)

    return restaurant


# Disable restaurant - Owner only
@router.patch("/{restaurant_id}/disable", response_model=RestaurantResponse)
def disable_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    restaurant.is_active = False

    db.commit()
    db.refresh(restaurant)

    return restaurant


# Get restaurant by ID - Public
@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    restaurant = db.get(Restaurant, restaurant_id)

    if restaurant is None or not restaurant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )

    return restaurant


# Update own restaurant - Restaurant Owner only
@router.put("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    update_data = restaurant_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(restaurant, field, value)

    db.commit()
    db.refresh(restaurant)

    return restaurant


# Deactivate own restaurant - Restaurant Owner only
@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = get_owned_restaurant(restaurant_id, current_user, db)

    restaurant.is_active = False

    db.commit()

    return {
        "message": "Restaurant deactivated successfully"
    }
