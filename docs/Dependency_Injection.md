# Dependency Injection in FastAPI

Dependency Injection (DI) is a software design pattern where an object or function receives other objects or functions that it depends on, rather than creating them itself.

FastAPI is famous for having one of the most powerful and intuitive Dependency Injection systems in modern web frameworks. We use it extensively for fetching database sessions and verifying user authentication.

---

## 1. The Manual Way (Without `Annotated`)

Before Python 3.9 brought widespread adoption of `typing.Annotated`, developers used the `Depends` class directly inside the default arguments of route signatures.

If you don't use `Annotated`, your code looks like this:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

# 1. We must declare both the type hint (Session) AND the default value (Depends(get_db))
@router.get("/todos")
async def read_todos(db: Session = Depends(get_db)):
    return db.query(Todos).all()
```

### The Problem with the Manual Way
1. **Repetitive (Not DRY):** If you have 50 endpoints that need a database connection, you have to type `db: Session = Depends(get_db)` 50 times.
2. **Type Hinting Conflicts:** In pure Python type theory, saying a variable equals a function call (`db = Depends()`) is messy because `Depends()` returns a FastAPI class, but we are telling Python `db` is of type `Session`. FastAPI magically resolves this at runtime, but from a strict typing perspective, it's hacky.

---

## 2. The Modern Way (Using `Annotated`)

Python 3.9 introduced `Annotated`, which allows you to attach "metadata" to a type hint without breaking static type checkers (like `mypy`).

In our project, we declared dependencies cleanly at the top of the file:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

# We define the dependency exactly ONCE
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

# We use it simply and cleanly
@router.get("/todos")
async def read_todos(user: user_dependency, db: db_dependency):
    return db.query(Todos).all()
```

### How `Annotated` Helps
- **DRY Code:** You declare the dependency logic once and reuse it across 100 endpoints by just typing `user: user_dependency`.
- **Cleaner Signatures:** Your endpoint signatures are much shorter and easier to read.
- **Type Checker Friendly:** `Annotated[Session, Depends(get_db)]` tells the IDE and mypy: *"This variable is literally just a `Session` (ignore the metadata for type checking)."* This provides flawless auto-complete without causing warnings.

---

## 3. How Dependency Injection Works Behind the Scenes

When you write `@router.get("/todos")` and add `user_dependency` to the function signature, FastAPI does a tremendous amount of invisible work before executing your endpoint logic.

Here is the exact step-by-step process behind the scenes:

1. **Introspection (At Startup):**
   When Uvicorn starts the server, FastAPI inspects the Python signatures of every single route function. It spots the `Depends()` metadata sitting natively inside `db_dependency` and `user_dependency`.

2. **Graph Construction:**
   FastAPI builds a "Dependency Graph." It notices that `get_current_user` requires an `oauth2_bearer` token, which itself is a dependency that requires reading the HTTP headers. It maps out exactly what needs to run, and in what order.

3. **Execution (At Request Time):**
   When a user makes a GET request to `/todos`, FastAPI blocks the route from running and starts executing the dependency graph:
   - It reads the `Authorization: Bearer <token>` from the HTTP Request.
   - It executes `get_current_user`, passing the token in. The function decodes the JWT and returns a Python dictionary `{"id": 5, "role": "admin"}`.
   - It executes `get_db()`. `get_db` opens a Postgres connection, `yields` the session, and pauses.

4. **Injection:**
   FastAPI takes the outputs of these functions (the user dictionary and the database session) and injects them directly into the arguments of `read_todos(user, db)`.

5. **Route Execution:**
   Your business logic runs identically to a standard Python function, using the pre-prepared database session and verified user dictionary.

6. **Cleanup (The `finally` block):**
   After your route returns the JSON response to the user, FastAPI remembers that `get_db()` yielded instead of returned. It goes back to `get_db()` and executes the `finally:` block, triggering `db.close()`, which safely returns the connection to the Postgres connection pool.
