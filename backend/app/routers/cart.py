from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.menu_item import MenuItem
from app.models.menu_category import MenuCategory
from app.models.restaurant import Restaurant
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
)


router = APIRouter(prefix="/cart", tags=["Cart Management"])


# Build cart response with calculated totals
def build_cart_response(cart: Cart, db: Session):
    cart_items = (
        db.query(CartItem, MenuItem.name)
        .join(MenuItem, CartItem.menu_item_id == MenuItem.id)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    items = []
    total_amount = Decimal("0.00")

    for cart_item, item_name in cart_items:
        subtotal = cart_item.unit_price * cart_item.quantity
        total_amount += subtotal

        items.append(
            CartItemResponse(
                id=cart_item.id,
                menu_item_id=cart_item.menu_item_id,
                item_name=item_name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                subtotal=subtotal,
            )
        )

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        restaurant_id=cart.restaurant_id,
        items=items,
        total_amount=total_amount,
    )


# Add food item to cart
@router.post("/add", response_model=CartResponse)
def add_to_cart(
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    menu_item = (
        db.query(MenuItem)
        .join(MenuCategory)
        .join(Restaurant)
        .filter(
            MenuItem.id == item_data.menu_item_id,
            MenuItem.is_available.is_(True),
            MenuCategory.is_active.is_(True),
            Restaurant.is_active.is_(True),
        )
        .first()
    )

    if not menu_item:
        raise HTTPException(
            status_code=404,
            detail="Food item not found or unavailable",
        )

    restaurant_id = (
        db.query(MenuCategory.restaurant_id)
        .filter(MenuCategory.id == menu_item.category_id)
        .scalar()
    )

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        cart = Cart(
            user_id=current_user.id,
            restaurant_id=restaurant_id,
        )
        db.add(cart)
        db.flush()

    elif cart.restaurant_id != restaurant_id:
        existing_items = db.query(CartItem).filter(
            CartItem.cart_id == cart.id
        ).count()

        if existing_items > 0:
            raise HTTPException(
                status_code=400,
                detail="Your cart contains items from another restaurant. Clear your cart first.",
            )

        cart.restaurant_id = restaurant_id

    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.menu_item_id == menu_item.id,
    ).first()

    if existing_item:
        existing_item.quantity += item_data.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            menu_item_id=menu_item.id,
            quantity=item_data.quantity,
            unit_price=menu_item.price,
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart)

    return build_cart_response(cart, db)


# View customer's cart
@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart is empty")

    return build_cart_response(cart, db)


# Update cart item quantity
@router.put("/items/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    cart_item = (
        db.query(CartItem)
        .join(Cart)
        .filter(
            CartItem.id == item_id,
            Cart.user_id == current_user.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    cart_item.quantity = item_data.quantity

    db.commit()

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    return build_cart_response(cart, db)


# Remove one item from cart
@router.delete("/items/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    cart_item = (
        db.query(CartItem)
        .join(Cart)
        .filter(
            CartItem.id == item_id,
            Cart.user_id == current_user.id,
        )
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    db.delete(cart_item)
    db.flush()

    remaining_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).count()

    if remaining_items == 0:
        cart.restaurant_id = None

    db.commit()

    return {"message": "Cart item removed successfully"}


# Clear entire cart
@router.delete("/clear")
def clear_cart(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart is already empty")

    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete(synchronize_session=False)

    cart.restaurant_id = None

    db.commit()

    return {"message": "Cart cleared successfully"}
