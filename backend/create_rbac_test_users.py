import secrets
from sqlalchemy import select

from app.database.connection import SessionLocal
from app.core.security import hash_password
from app.models import Role, User


TEST_USERS = [
    {
        "username": "rbac_owner_test",
        "email": "rbac_owner_test@example.com",
        "full_name": "Restaurant Owner Test",
        "role": "RESTAURANT_OWNER",
    },
    {
        "username": "rbac_delivery_test",
        "email": "rbac_delivery_test@example.com",
        "full_name": "Delivery Partner Test",
        "role": "DELIVERY_PARTNER",
    },
    {
        "username": "rbac_admin_test",
        "email": "rbac_admin_test@example.com",
        "full_name": "Admin Test",
        "role": "ADMIN",
    },
]


def create_test_users():
    db = SessionLocal()

    try:
        for item in TEST_USERS:
            existing = db.scalar(
                select(User).where(
                    (User.username == item["username"])
                    | (User.email == item["email"])
                )
            )

            if existing:
                print(f"SKIPPED: {item['username']} already exists.")
                continue

            role = db.scalar(
                select(Role).where(Role.name == item["role"])
            )

            if not role:
                raise ValueError(f"Role not found: {item['role']}")

            password = secrets.token_urlsafe(18)

            user = User(
                username=item["username"],
                email=item["email"],
                full_name=item["full_name"],
                password_hash=hash_password(password),
                role_id=role.id,
                is_active=True,
            )

            db.add(user)
            db.flush()

            print("\nAccount created:")
            print("Username:", item["username"])
            print("Email:", item["email"])
            print("Role:", item["role"])
            print("Temporary password:", password)

        db.commit()
        print("\nTest account creation completed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_test_users()
