# FoodieExpress – Entity Relationship Diagram

The following ER diagram represents the main database tables and their relationships.

```mermaid
erDiagram
    ROLES ||--o{ USERS : assigns
    USERS ||--o{ AUTH_SESSIONS : has
    USERS ||--o{ PASSWORD_RESET_TOKENS : requests
    USERS ||--o{ RESTAURANTS : owns
    USERS ||--o{ CARTS : has
    USERS ||--o{ ORDERS : places
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ DELIVERIES : handles
    USERS ||--o{ PAYMENTS : makes
    USERS ||--o{ REVIEWS : writes

    RESTAURANTS ||--o{ MENU_CATEGORIES : contains
    RESTAURANTS ||--o{ ORDERS : receives
    RESTAURANTS ||--o{ REVIEWS : receives

    MENU_CATEGORIES ||--o{ MENU_ITEMS : contains

    CARTS ||--o{ CART_ITEMS : contains
    MENU_ITEMS ||--o{ CART_ITEMS : added_to

    ORDERS ||--o{ ORDER_ITEMS : contains
    MENU_ITEMS ||--o{ ORDER_ITEMS : ordered_as

    ORDERS ||--o| DELIVERIES : has
    ORDERS ||--o| PAYMENTS : has
    ORDERS ||--o| REVIEWS : receives

    ROLES {
        int id PK
        varchar name
    }

    USERS {
        int id PK
        int role_id FK
        varchar username
        varchar email
        varchar password_hash
    }

    AUTH_SESSIONS {
        int id PK
        int user_id FK
    }

    PASSWORD_RESET_TOKENS {
        int id PK
        int user_id FK
    }

    RESTAURANTS {
        int id PK
        int owner_id FK
        varchar name
        varchar address
        varchar city
        boolean is_active
    }

    MENU_CATEGORIES {
        int id PK
        int restaurant_id FK
        varchar name
    }

    MENU_ITEMS {
        int id PK
        int category_id FK
        varchar name
        decimal price
    }

    CARTS {
        int id PK
        int user_id FK
    }

    CART_ITEMS {
        int id PK
        int cart_id FK
        int menu_item_id FK
        int quantity
    }

    ORDERS {
        int id PK
        int customer_id FK
        int restaurant_id FK
    }

    ORDER_ITEMS {
        int id PK
        int order_id FK
        int menu_item_id FK
        int quantity
    }

    DELIVERIES {
        int id PK
        int order_id FK
        int delivery_partner_id FK
    }

    PAYMENTS {
        int id PK
        int order_id FK
        int customer_id FK
    }

    REVIEWS {
        int id PK
        int order_id FK
        int customer_id FK
        int restaurant_id FK
    }

    NOTIFICATIONS {
        int id PK
        int user_id FK
    }
```

**Note:** This is a high-level relationship diagram. Confirm the exact column names and cardinalities against your SQL schema before treating it as the final database specification.