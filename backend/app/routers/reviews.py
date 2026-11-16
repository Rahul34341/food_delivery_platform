from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_role
from app.models import Review, Order, Restaurant, User
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/reviews", tags=["Review Management"])


@router.post("/", response_model=ReviewResponse)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("CUSTOMER")),
):
    # Verify that the order belongs to the logged-in customer.
    order = db.query(Order).filter(
        Order.id == review_data.order_id,
        Order.customer_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    # Only delivered orders can be reviewed.
    if order.status != "DELIVERED":
        raise HTTPException(
            status_code=400,
            detail="You can review an order only after it is delivered",
        )

    # Prevent multiple reviews for the same order.
    existing_review = db.query(Review).filter(
        Review.order_id == order.id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=409,
            detail="You have already reviewed this order",
        )

    review = Review(
        order_id=order.id,
        customer_id=current_user.id,
        restaurant_id=order.restaurant_id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(review)

    try:
        db.commit()
        db.refresh(review)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create review. A review may already exist for this order.",
        )

    return review


@router.get("/my-reviews", response_model=list[ReviewResponse])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("CUSTOMER")),
):
    return (
        db.query(Review)
        .filter(Review.customer_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.get(
    "/restaurant/{restaurant_id}",
    response_model=list[ReviewResponse],
)
def get_restaurant_reviews(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("RESTAURANT_OWNER")),
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.owner_id == current_user.id,
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    return (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )
