from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models import Delivery, Order, Restaurant, User
from app.schemas.delivery import (
    DeliveryAssign,
    DeliveryStatusUpdate,
    DeliveryResponse,
)

router = APIRouter(prefix="/deliveries", tags=["Delivery Management"])


@router.post("/assign", response_model=DeliveryResponse)
def assign_delivery(
    assignment: DeliveryAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    order = (
        db.query(Order)
        .join(Restaurant, Order.restaurant_id == Restaurant.id)
        .filter(
            Order.id == assignment.order_id,
            Restaurant.owner_id == current_user.id,
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != "READY_FOR_PICKUP":
        raise HTTPException(
            status_code=400,
            detail="Order must be READY_FOR_PICKUP before assigning delivery",
        )

    partner = db.query(User).filter(
        User.id == assignment.delivery_partner_id,
        User.is_active == True,
    ).first()

    if not partner or not partner.role or partner.role.name != "DELIVERY_PARTNER":
        raise HTTPException(
            status_code=400,
            detail="Invalid or inactive delivery partner",
        )

    existing_delivery = db.query(Delivery).filter(
        Delivery.order_id == order.id
    ).first()

    if existing_delivery:
        raise HTTPException(
            status_code=409,
            detail="A delivery partner is already assigned to this order",
        )

    delivery = Delivery(
        order_id=order.id,
        delivery_partner_id=partner.id,
        status="ASSIGNED",
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


@router.get("/my-deliveries", response_model=list[DeliveryResponse])
def get_my_deliveries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("DELIVERY_PARTNER")),
):
    return (
        db.query(Delivery)
        .filter(Delivery.delivery_partner_id == current_user.id)
        .order_by(Delivery.created_at.desc())
        .all()
    )


@router.patch("/{delivery_id}/status", response_model=DeliveryResponse)
def update_delivery_status(
    delivery_id: int,
    status_data: DeliveryStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("DELIVERY_PARTNER")),
):
    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id,
        Delivery.delivery_partner_id == current_user.id,
    ).first()

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    transitions = {
        "ASSIGNED": ["ACCEPTED", "REJECTED"],
        "ACCEPTED": ["PICKED_UP"],
        "PICKED_UP": ["OUT_FOR_DELIVERY"],
        "OUT_FOR_DELIVERY": ["DELIVERED"],
    }

    new_status = status_data.status

    if new_status not in transitions.get(delivery.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change delivery status from {delivery.status} to {new_status}",
        )

    order = db.query(Order).filter(Order.id == delivery.order_id).first()

    if new_status == "REJECTED":
        delivery.status = "REJECTED"
    elif new_status == "PICKED_UP":
        delivery.status = "PICKED_UP"
        delivery.picked_up_at = datetime.utcnow()
        order.status = "OUT_FOR_DELIVERY"
    elif new_status == "OUT_FOR_DELIVERY":
        delivery.status = "OUT_FOR_DELIVERY"
        order.status = "OUT_FOR_DELIVERY"
    elif new_status == "DELIVERED":
        delivery.status = "DELIVERED"
        delivery.delivered_at = datetime.utcnow()
        order.status = "DELIVERED"
    else:
        delivery.status = new_status

    db.commit()
    db.refresh(delivery)

    return delivery
