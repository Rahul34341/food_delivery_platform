from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, hash_refresh_token, generate_session_id
from app.schemas.auth import TokenResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User, Role, AuthSession, PasswordResetToken
from app.schemas.auth import UserRegister, UserResponse, UserLogin, TokenResponse
from app.core.security import hash_password
from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_role
from jose import JWTError

from app.core.security import (
    decode_token,
)
from app.schemas.auth import RefreshTokenRequest

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import decode_token
from app.core.security import (
    generate_password_reset_token,
    hash_password_reset_token
)
from app.schemas.auth import (
    PasswordResetRequest,
    PasswordResetConfirm
)

from app.schemas.auth import ProfileUpdate
from app.schemas.auth import ChangePassword


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    # Normalize email and username
    email = user_data.email.lower()
    username = user_data.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty"
        )

    # Check existing email
    existing_email = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Check existing username
    existing_username = db.scalar(
        select(User).where(User.username == username)
    )

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already taken"
        )

    # Assign the role selected during registration
    selected_role = db.scalar(
    select(Role).where(Role.name == user_data.role)
    )

    if not selected_role:
     raise HTTPException(
        status_code=500,
        detail=f"{user_data.role} role is not configured"
    )

    # Create user with hashed password
    new_user = User(
    username=username,
    email=email,
    password_hash=hash_password(user_data.password),
    full_name=user_data.full_name.strip(),
    phone=user_data.phone,
    role_id=selected_role.id
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    return new_user



@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    email = user_data.email.lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not verify_password(
        user_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive"
        )

    # Generate unique session ID
    session_id = generate_session_id()

    # Generate refresh token
    refresh_token, expires_at = create_refresh_token(
        user_id=user.id,
        session_id=session_id
    )

    # Save refresh token hash in database
    auth_session = AuthSession(
        user_id=user.id,
        session_id=session_id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at.replace(tzinfo=None)
    )

    # Generate access token linked to this session
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.name,
            "sid": session_id
        }
    )

    try:
        db.add(auth_session)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create login session"
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    # Validate refresh token
    try:
        payload = decode_token(
            token_data.refresh_token,
            expected_type="refresh"
        )

        user_id = int(payload["sub"])
        session_id = payload["sid"]

    except (JWTError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    # Find active session
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.session_id == session_id,
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None)
        )
    )

    if not auth_session:
        raise HTTPException(
            status_code=401,
            detail="Session is invalid or revoked"
        )

    # Check token hash
    if auth_session.refresh_token_hash != hash_refresh_token(
        token_data.refresh_token
    ):
        raise HTTPException(
            status_code=401,
            detail="Refresh token has already been used"
        )

    # Check database expiry
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if auth_session.expires_at <= now:
        raise HTTPException(
            status_code=401,
            detail="Refresh token has expired"
        )

    user = db.get(User, user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User is unavailable"
        )

    # Generate rotated refresh token
    new_refresh_token, new_expires_at = create_refresh_token(
        user_id=user.id,
        session_id=session_id
    )

    # Generate new access token
    new_access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.name,
            "sid": session_id
        }
    )

    # Replace stored refresh token hash
    auth_session.refresh_token_hash = hash_refresh_token(
        new_refresh_token
    )
    auth_session.expires_at = new_expires_at.replace(tzinfo=None)

    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }


logout_security = HTTPBearer()


@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(logout_security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get session ID from access token
    try:
        payload = decode_token(
            credentials.credentials,
            expected_type="access"
        )
        session_id = payload["sid"]

    except (JWTError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

    # Find the user's active session
    auth_session = db.scalar(
        select(AuthSession).where(
            AuthSession.session_id == session_id,
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None)
        )
    )

    if not auth_session:
        raise HTTPException(
            status_code=401,
            detail="Session already revoked or not found"
        )

    # Revoke session
    auth_session.revoked_at = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

    db.commit()

    return {
        "message": "Logout successful. Session revoked."
    }


@router.post("/password-reset/request")
def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    email = request_data.email.lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    # Always return a generic response to avoid revealing registered emails.
    response = {
        "message": "If the account exists, a password reset link has been generated."
    }

    if not user or not user.is_active:
        return response

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Invalidate previous unused reset tokens.
    previous_tokens = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        )
    ).all()

    for old_token in previous_tokens:
        old_token.used_at = now

    # Generate a new one-time token.
    reset_token = generate_password_reset_token()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(reset_token),
        expires_at=now + timedelta(minutes=15)
    )

    db.add(reset_record)
    db.commit()

    # Return the token only in development for local Swagger testing.
    if settings.APP_ENV == "development":
        response["reset_token"] = reset_token

    return response


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    token_hash = hash_password_reset_token(reset_data.token)

    reset_record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None)
        )
    )

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used reset token"
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if reset_record.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="Password reset token has expired"
        )

    user = db.get(User, reset_record.user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Unable to reset password for this account"
        )

    # Update password and mark token as used.
    user.password_hash = hash_password(reset_data.new_password)
    reset_record.used_at = now

    # Revoke all existing login sessions for this user.
    active_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None)
        )
    ).all()

    for session in active_sessions:
        session.revoked_at = now

    db.commit()

    return {
        "message": "Password reset successful. Please log in again."
    }

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is None:
            continue

        if field == "username":
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Username cannot be empty"
                )

            existing = db.scalar(
                select(User).where(
                    User.username == value,
                    User.id != current_user.id
                )
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Username already taken"
                )

        elif field == "email":
            value = str(value).lower()

            existing = db.scalar(
                select(User).where(
                    User.email == value,
                    User.id != current_user.id
                )
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Email already registered"
                )

        elif field == "full_name":
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Full name cannot be empty"
                )

        setattr(current_user, field, value)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Profile information conflicts with another user"
        )

    return current_user

@router.get("/customer-area")
def customer_area(
    current_user: User = Depends(require_role("CUSTOMER"))
):
    return {
        "message": "Welcome to Customer Area",
        "username": current_user.username,
        "role": current_user.role.name
    }


@router.get("/restaurant-owner-area")
def restaurant_owner_area(
    current_user: User = Depends(require_role("RESTAURANT_OWNER"))
):
    return {
        "message": "Welcome to Restaurant Owner Area",
        "username": current_user.username,
        "role": current_user.role.name
    }


@router.get("/delivery-area")
def delivery_area(
    current_user: User = Depends(require_role("DELIVERY_PARTNER"))
):
    return {
        "message": "Welcome to Delivery Partner Area",
        "username": current_user.username,
        "role": current_user.role.name
    }


@router.get("/admin-area")
def admin_area(
    current_user: User = Depends(require_role("ADMIN"))
):
    return {
        "message": "Welcome to Admin Area",
        "username": current_user.username,
        "role": current_user.role.name
    }

@router.put("/change-password")
def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not verify_password(
        password_data.current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Prevent using the same password
    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password securely
    current_user.password_hash = hash_password(
        password_data.new_password
    )

    # Revoke all active sessions
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    active_sessions = db.scalars(
        select(AuthSession).where(
            AuthSession.user_id == current_user.id,
            AuthSession.revoked_at.is_(None)
        )
    ).all()

    for session in active_sessions:
        session.revoked_at = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change password"
        )

    return {
        "message": "Password changed successfully. Please log in again."
    }