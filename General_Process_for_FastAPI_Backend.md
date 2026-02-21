# General Process for Creating a FastAPI Backend

Based on the structure and features implemented in the `project-3` Todo Application, here is a general, step-by-step process you can follow to create robust FastAPI backend applications in the future.

---

## 1. Project Initialization & Structure Setup

Before writing any code, establish a clean directory structure and manage your dependencies.

**Steps:**
- Initialize the project with a package manager (e.g., `uv`, `poetry`, or standard `pip` + `requirements.txt`).
- This project utilizes `uv` as the package manager.
- Run `uv init` to initialize the project.
- Run `uv add <package_name>` to add dependencies.
- The main dependencies usually required are:
  - `fastapi` -> The main framework.
  - `uvicorn` -> ASGI server for running the application.
  - `sqlalchemy` -> ORM (Object-Relational Mapping) library for database interactions.
  - `psycopg2-binary` -> PostgreSQL database driver.
- Libraries like `starlette`, `pydantic` are pre-packaged with `fastapi` library.
- For authentication, we will use `passlib` and `pyjwt`.
- Set up the main application directory (e.g., `todoapp/`).
- Inside the main directory, create placeholders for your core architectural components:
  - `main.py`: The entry point.
  - `database.py`: Database connection rules.
  - `models.py`: SQLAlchemy database models.
  - `schemas.py`: Pydantic models for data validation.
  - `routers/`: Directory to hold modular route files (e.g., `auth.py`, `todos.py`).

---

## 2. Database Configuration (`database.py`)

Set up the connection to your underlying database.

**Steps:**
- Import `create_engine`, `sessionmaker`, and `declarative_base` from `sqlalchemy`.
- Define your Database URL (e.g., `postgresql://user:password@localhost/dbname`).
- Create the SQLAlchemy engine.
- Create a `SessionLocal` class using `sessionmaker()`, bound to the engine. This will be used to generate database sessions for each request.
- Create a `Base` object using `declarative_base()`. All your database models will inherit from this base.

---

## 3. Data Modeling (`models.py`)

Translate your application entities into database tables using the SQLAlchemy ORM.

**Steps:**
- Import the `Base` object from `database.py`.
- Define classes that inherit from `Base` (e.g., `class Users(Base):`, `class Todos(Base):`).
- Add the `__tablename__` attribute to specify the exact table name in the database.
- Define columns using `Column`, `Integer`, `String`, `Boolean`, etc.
- Set up Primary Keys (`primary_key=True, index=True`).
- Define relationships and foreign keys (e.g., `owner_id = Column(Integer, ForeignKey("users.id"))`).

---

## 4. Schemas for Request & Response Validation (Pydantic)

FastAPI relies on Pydantic to validate incoming JSON payloads and format outward responses.

**Steps:**
- Create Pydantic classes inheriting from `BaseModel`.
- Define the fields exactly as you expect them from the client (e.g., `title: str`, `priority: int`).
- Use Pydantic's `Field` to enforce constraints. For example, `Field(min_length=3)`, `Field(gt=0, lt=6)`.
- Use these schemas as parameter types in your routing functions.

*(Note: In smaller projects, schemas are sometimes written directly inside the router files, but abstracting them to `schemas.py` is cleaner as the project grows).*

---

## 5. Dependency Injection

FastAPI's `Depends` system allows you to reuse logic across different routes seamlessly.

**Steps:**
- **Database Dependency:** Create a `get_db()` generator function that yields a `SessionLocal()` object and ensures it is closed in a `finally` block. Create an annotated variable (e.g., `db_dependency = Annotated[Session, Depends(get_db)]`) to inject the database session into routes.
- **Auth Dependency:** Create a `get_current_user` function that extracts a token, decodes it, and returns user data (more details in step 6).

---

## 6. Authentication & Security Setup (`auth.py`)

Handle user registration, login, and secure route access using JSON Web Tokens (JWT).

**Steps:**
- **Password Hashing:** Use `passlib` (`CryptContext(schemes=['bcrypt'])`) to hash passwords before storing them in the DB.
- **OAuth2 Flow:** Use `OAuth2PasswordBearer` to indicate where the client should send login credentials (e.g., `/auth/token`).
- **Token Generation:** Use the `PyJWT` library to sign a payload (containing `user_id`, `username`, `role`, and expiration time) using a `SECRET_KEY` and `ALGORITHM` (like HS256). Combine this in an endpoint that receives `OAuth2PasswordRequestForm` and returns the access token.
- **Token Verification:** The `get_current_user` dependency will intercept the token provided by `OAuth2PasswordBearer`, decode it with the `SECRET_KEY`, and raise a `401 Unauthorized` `HTTPException` if invalid.

---

## 7. Modular Routers (`routers/`)

Keep your codebase organized by splitting endpoints into related modules rather than cluttering `main.py`.

**Steps:**
- Inside a router file (e.g., `todos.py`), import `APIRouter()` and configure prefixes and tags: `router = APIRouter(prefix="/todos", tags=["todos"])`.
- Write your endpoints using decorators (`@router.get`, `@router.post`, etc.).
- Inject your dependencies into the route functions:
  ```python
  @router.get("/")
  async def read_all(user: user_dependency, db: db_dependency):
      # ... logic
  ```
- Use SQLAlchemy queries to perform CRUD operations (e.g., `db.query(Todos).filter(...).first()`).
- Always `db.add()` and `db.commit()` when manipulating data.
- Return explicit HTTP status codes using Starlette's `status` enum (e.g., `status_code=status.HTTP_201_CREATED`).

---

## 8. Main Application Wiring (`main.py`)

Tie everything together into the FastAPI application instance.

**Steps:**
- Instantiate the application: `app = FastAPI()`.
- Use `models.Base.metadata.create_all(bind=engine)` to instruct SQLAlchemy to create the tables in the database if they don't already exist. *(Note: in production apps, consider using migration tools like `Alembic` instead).*
- Import your routers from the routers folder.
- Register the routers with your application: `app.include_router(routers.auth.router)`, etc.

---

## Flowchart: General Process & Request Lifecycle

```mermaid
flowchart TD
    A[Start Project Setup] --> B(Create Virtual Environment & Install Dependencies)
    B --> C(Set up modular structure: main, models, db, routers)
    
    C --> D[Database Config database.py]
    D --> E(Define Engine & SessionLocal)
    E --> F[Data Modeling models.py]
    F --> G(Create SQLAlchemy Tables)
    
    G --> H[Pydantic Schemas - Validation]
    H --> I[Dependency Injection]
    I --> J(Database Session Generator get_db)
    
    J --> K[Authentication auth.py]
    K --> L(Password Hashing & JWT Logic)
    
    L --> M[Build Routers]
    M --> N(User Routers)
    M --> O(Todo Routers)
    M --> P(Admin Routers)
    
    N --> Q[Main App Wiring main.py]
    O --> Q
    P --> Q
    
    Q --> R(app = FastAPI)
    R --> S(Create DB tables: metadata.create_all)
    S --> T(Include Routers: app.include_router)
    
    T --> U((App Ready! Run with Uvicorn))
```

### Request Flow for a Protected Route

```mermaid
sequenceDiagram
    participant Client as Client/Browser
    participant FastAPI as FastAPI Route
    participant Auth as get_current_user()
    participant DB as Postgres Database

    Client->>FastAPI: GET /todos (with Bearer Token)
    Note over FastAPI,Auth: Dependency Execution
    FastAPI->>Auth: Pass Token
    Auth-->>Auth: Decode JWT & Verify Secret
    Auth-->>FastAPI: Return User Dict (id, role)
    Note over FastAPI,DB: Route Logic Execution
    FastAPI->>DB: Query Todos where owner_id = User.id
    DB-->>FastAPI: Return Todo Records
    FastAPI-->>Client: 200 OK + JSON Response
```
