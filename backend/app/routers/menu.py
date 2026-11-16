from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.restaurant import Restaurant
from app.models.menu_category import MenuCategory
from app.schemas.menu import MenuCategoryCreate, MenuCategoryUpdate, MenuCategoryResponse
from app.models.menu_item import MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse


router = APIRouter(prefix="/menu", tags=["Menu Management"])


# Create a menu category
@router.post(
    "/restaurants/{restaurant_id}/categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_category(
    restaurant_id: int,
    category_data: MenuCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id,
        Restaurant.is_active == True,
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found or you do not own this restaurant",
        )

    category = MenuCategory(
        restaurant_id=restaurant_id,
        name=category_data.name,
        description=category_data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# Get active categories for a restaurant
@router.get(
    "/restaurants/{restaurant_id}/categories",
    response_model=list[MenuCategoryResponse],
)
def get_menu_categories(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.is_active == True,
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    categories = db.query(MenuCategory).filter(
        MenuCategory.restaurant_id == restaurant_id,
        MenuCategory.is_active == True,
    ).all()

    return categories


# Update a menu category
@router.put(
    "/categories/{category_id}",
    response_model=MenuCategoryResponse,
)
def update_menu_category(
    category_id: int,
    category_data: MenuCategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    category = db.query(MenuCategory).join(Restaurant).filter(
        MenuCategory.id == category_id,
        Restaurant.owner_id == current_user.id,
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category


# Deactivate a menu category
@router.delete(
    "/categories/{category_id}",
)
def deactivate_menu_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    category = db.query(MenuCategory).join(Restaurant).filter(
        MenuCategory.id == category_id,
        Restaurant.owner_id == current_user.id,
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_active = False

    db.commit()

    return {"message": "Menu category deactivated successfully"}


# ---------------------------------
# MENU ITEM MANAGEMENT
# ---------------------------------

# Add a food item to a category
@router.post(
    "/categories/{category_id}/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_menu_item(
    category_id: int,
    item_data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    category = db.query(MenuCategory).join(Restaurant).filter(
        MenuCategory.id == category_id,
        MenuCategory.is_active == True,
        Restaurant.owner_id == current_user.id,
        Restaurant.is_active == True,
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found or you do not own this restaurant",
        )

    item = MenuItem(
        category_id=category_id,
        name=item_data.name,
        description=item_data.description,
        price=item_data.price,
        image_url=item_data.image_url,
        is_vegetarian=item_data.is_vegetarian,
        preparation_time_minutes=item_data.preparation_time_minutes,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# Get available food items in a category
@router.get(
    "/categories/{category_id}/items",
    response_model=list[MenuItemResponse],
)
def get_menu_items(
    category_id: int,
    db: Session = Depends(get_db),
):
    category = db.query(MenuCategory).join(Restaurant).filter(
        MenuCategory.id == category_id,
        MenuCategory.is_active == True,
        Restaurant.is_active == True,
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    items = db.query(MenuItem).filter(
        MenuItem.category_id == category_id,
        MenuItem.is_available == True,
    ).all()

    return items


# Update a food item
@router.put(
    "/items/{item_id}",
    response_model=MenuItemResponse,
)
def update_menu_item(
    item_id: int,
    item_data: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    item = db.query(MenuItem).join(MenuCategory).join(Restaurant).filter(
        MenuItem.id == item_id,
        Restaurant.owner_id == current_user.id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    update_data = item_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


# Mark a food item as unavailable
@router.delete("/items/{item_id}")
def deactivate_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    item = db.query(MenuItem).join(MenuCategory).join(Restaurant).filter(
        MenuItem.id == item_id,
        Restaurant.owner_id == current_user.id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    item.is_available = False

    db.commit()

    return {"message": "Menu item marked as unavailable successfully"}
