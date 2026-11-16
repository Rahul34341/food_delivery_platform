from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models import Order, Payment, User
from app.schemas.payment import PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payment Management"])


@router.post("/", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("CUSTOMER")),
):
    # Verify that the order belongs to the logged-in customer.
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.customer_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if order.status == "CANCELLED":
        raise HTTPException(
            status_code=400,
            detail="Payment cannot be made for a cancelled order",
        )

    # Check whether payment already exists.
    existing_payment = db.query(Payment).filter(
        Payment.order_id == order.id
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="Payment already exists for this order",
        )

    # Simulated payment processing.
    if payment_data.payment_method == "COD":
        payment_status = "PENDING"
        transaction_id = None
        paid_at = None
    else:
        payment_status = "SUCCESS"
        transaction_id = f"TXN-{uuid4().hex[:16].upper()}"
        paid_at = datetime.utcnow()

    payment = Payment(
        order_id=order.id,
        customer_id=current_user.id,
        amount=order.total_amount,
        payment_method=payment_data.payment_method,
        transaction_id=transaction_id,
        status=payment_status,
        paid_at=paid_at,
    )

    try:
        db.add(payment)
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to process payment",
        )

    return payment


@router.get("/my-payments", response_model=list[PaymentResponse])
def get_my_payments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("CUSTOMER")),
):
    return (
        db.query(Payment)
        .filter(Payment.customer_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("CUSTOMER")),
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.customer_id == current_user.id,
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return payment
