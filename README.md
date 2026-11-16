# FoodieExpress – Food Delivery Platform

## Project Overview

FoodieExpress is a web-based food delivery platform that connects customers, restaurant owners, and delivery partners. It provides user authentication, restaurant management, and APIs for managing food delivery operations.

## Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication

### Database
- MySQL
- Alembic Database Migrations

## Project Features

- User registration and login
- JWT-based authentication
- Role-based access control
- Customer, restaurant owner, delivery partner, and admin roles
- User profile management
- Password change and password reset
- Restaurant registration and management
- Restaurant logo and banner uploads
- Restaurant enable and disable functionality
- Database schema and migration management
- Interactive API documentation

## Project Structure

```text
food_delivery_platform/
├── backend/
│   ├── app/
│   ├── alembic/
│   │   └── versions/
│   ├── uploads/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── assets/
│   │   ├── css/
│   │   ├── images/
│   │   └── js/
│   ├── pages/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── profile.html
└── docs/
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd food_delivery_platform
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the backend directory.

Configure the following variables with your local values:

```env
DATABASE_URL=your_mysql_database_url
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://127.0.0.1:5500
APP_ENV=development
DEBUG=True
```

Do not upload your actual `.env` file or secret keys to GitHub.

### 5. Create the MySQL Database

Create a MySQL database named:

```sql
CREATE DATABASE food_delivery_db;
```

Configure the database connection in the backend `.env` file.

### 6. Apply Database Migrations

From the backend directory, run:

```bash
alembic upgrade head
```

### 7. Start the Backend Server

Run the FastAPI application using its configured application entry point.

The backend API is expected to be available at:

```text
http://127.0.0.1:8000
```

### 8. Start the Frontend

Open another terminal from the project root and run:

```bash
python -m http.server 5500 --directory frontend
```

Open the frontend:

```text
http://127.0.0.1:5500/index.html
```

## API Documentation

FastAPI provides interactive API documentation.

**Swagger UI:**

http://127.0.0.1:8000/docs

**ReDoc:**

http://127.0.0.1:8000/redoc

## Database and Migration Files

- Database schema export: `docs/database_schema.sql`
- Alembic configuration: `backend/alembic.ini`
- Migration scripts: `backend/alembic/versions/`
- Migration status can be checked using:

```bash
alembic current
```

## Project Documentation

Additional project proof files are maintained in the `docs/` directory, including database schema, migration structure, and API documentation screenshots.

## Security Notes

- Passwords are stored as secure hashes.
- JWT tokens are used for authentication.
- Role-based access controls protect restricted operations.
- Environment variables are used for sensitive configuration.
- Never commit passwords, secret keys, or access tokens to source control.

## Project Name

**FoodieExpress – Food Delivery Platform**