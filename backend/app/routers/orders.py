from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.dependencies.auth import require_role

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant

from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)

router = APIRouter(prefix="/orders", tags=["Order Management"])


# Place an order using the customer's cart
@router.post("/", response_model=OrderResponse)
def place_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    cart = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_items = (
        db.query(CartItem, MenuItem)
        .join(MenuItem, CartItem.menu_item_id == MenuItem.id)
        .filter(CartItem.cart_id == cart.id)
        .all()
    )

    if not cart_items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    restaurant = db.query(Restaurant).filter(
        Restaurant.id == cart.restaurant_id,
        Restaurant.is_active.is_(True),
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=400,
            detail="Restaurant is unavailable",
        )

    total_amount = Decimal("0.00")

    for cart_item, menu_item in cart_items:
        if not menu_item.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"{menu_item.name} is currently unavailable",
            )

        subtotal = cart_item.unit_price * cart_item.quantity
        total_amount += subtotal

    try:
        order = Order(
            customer_id=current_user.id,
            restaurant_id=restaurant.id,
            delivery_address=order_data.delivery_address,
            contact_phone=order_data.contact_phone,
            total_amount=total_amount,
            status="PLACED",
        )

        db.add(order)
        db.flush()

        for cart_item, menu_item in cart_items:
            subtotal = cart_item.unit_price * cart_item.quantity

            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                subtotal=subtotal,
            )

            db.add(order_item)

        db.query(CartItem).filter(
            CartItem.cart_id == cart.id
        ).delete(synchronize_session=False)

        cart.restaurant_id = None

        db.commit()

        saved_order = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.id == order.id)
            .first()
        )

        return saved_order

    except Exception:
        db.rollback()
        raise


# View customer's order history
@router.get("/my-orders", response_model=list[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.customer_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# View orders belonging to the restaurant owner's restaurants
@router.get("/restaurant/orders", response_model=list[OrderResponse])
def get_restaurant_orders(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    orders = (
        db.query(Order)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .options(joinedload(Order.items))
        .filter(Restaurant.owner_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return orders


# View one order
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(
            Order.id == order_id,
            Order.customer_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


# Cancel an order before restaurant confirmation
@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("CUSTOMER")),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.customer_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "PLACED":
        raise HTTPException(
            status_code=400,
            detail="Only placed orders can be cancelled",
        )

    order.status = "CANCELLED"
    db.commit()

    return {"message": "Order cancelled successfully"}


# Update order status (restaurant owner only)
@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("RESTAURANT_OWNER")),
):
    order = (
        db.query(Order)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .options(joinedload(Order.items))
        .filter(
            Order.id == order_id,
            Restaurant.owner_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed_statuses = [
        "CONFIRMED",
        "PREPARING",
        "READY_FOR_PICKUP",
    ]

    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Restaurant owners can only set CONFIRMED, PREPARING, or READY_FOR_PICKUP",
        )

    if order.status in ["CANCELLED", "DELIVERED"]:
        raise HTTPException(
            status_code=400,
            detail="This order cannot be updated",
        )

    order.status = status_data.status
    db.commit()
    db.refresh(order)

    return order
