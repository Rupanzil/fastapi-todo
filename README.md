# FastAPI Todo Application

This project is part of a FastAPI tutorial (based on a Udemy course by Eric Roby). It serves as a practical implementation to build mental models and retain core FastAPI concepts.

## Broad-Based Topics Covered

This project demonstrates several foundational and advanced FastAPI topics:

1. **FastAPI Application & Routing Strategies**
   - Application instantiation and configuration.
   - Modular routing using `APIRouter` to separate concerns (`auth`, `todos`, `users`, `admin`).
2. **Database Integration (SQLAlchemy)**
   - Configuring a PostgreSQL database connection.
   - Using ORM concepts (`declarative_base`, `sessionmaker`, `models`).
   - Handling database sessions per request using dependency injection (`yield db`).
3. **Authentication & Authorization (JWT & OAuth2)**
   - Implementing OAuth2 with Password (and Bearer) flow (`OAuth2PasswordBearer`, `OAuth2PasswordRequestForm`).
   - Password hashing and verification using `passlib` and `bcrypt`.
   - Generating and decoding JSON Web Tokens (JWT) for stateless authentication.
   - Role-Based Access Control (RBAC), restricting specific endpoints (like `/admin/*`) to users with the 'admin' role.
4. **Data Validation and Schemas (Pydantic)**
   - Defining schemas for request and response payloads.
   - Enforcing data integrity using Pydantic `Field` arguments (e.g., `min_length`, `max_length`, `gt`).
5. **Path & Query Parameters**
   - Validating endpoint URL parameters using FastAPI's `Path` and ensuring integer constraints (e.g., `gt=0`).
6. **Dependency Injection (`Depends`)**
   - Reusable dependencies for fetching the database session (`get_db`).
   - Custom dependencies for extracting and verifying the current active user from the JWT (`get_current_user`).
7. **HTTP Status Codes & Exception Handling**
   - Explicitly returning appropriate success codes (`201 Created`, `204 No Content`, `200 OK`).
   - Throwing `HTTPException` for authentication failures (401), not found errors (404), etc.

## Setup Instructions

1. Ensure you have Python `>=3.13` installed.
2. The project uses `pyproject.toml` and `uv.lock`. You can install the dependencies using `uv` or `pip`:
   ```bash
   uv sync
   # OR
   pip install -e .
   ```
3. Ensure PostgreSQL is running locally. Set up a database named `TodoApplicationDatabase` and use the connection string configured in `database.py`:
   `postgresql://postgres:test1234@localhost/TodoApplicationDatabase`
4. Start the FastAPI development server:
   ```bash
   cd todoapp
   uvicorn main:app --reload
   ```
5. Navigate to `http://127.0.0.1:8000/docs` in your browser to access the interactive Swagger UI and test the endpoints.
