# Pydantic and Data Validation in FastAPI

FastAPI is built heavily on **Pydantic**, a data validation and settings management library for Python that uses type hints to validate and parse data. 

Whenever a client sends JSON data in a POST or PUT request, Pydantic intercepts it, checks if it meets your strict rules, and transforms it into a Python object you can safely use.

---

## 1. How it Helps
- **Security & Integrity:** It ensures your app never processes malicious or malformed data. If a user tries to pass an empty string for their "username" or a string "twenty" into an integer "age" field, Pydantic stops them before the code in your endpoint even runs.
- **Automatic Documentation:** Pydantic models automatically translate into OpenAPI/Swagger documentation, so the interactive API docs at `/docs` know exactly what fields are required.
- **Data Coercion:** If a client sends `{"priority": "5"}` (a string), Pydantic is smart enough to convert it into the integer `5` because you typed it as `priority: int`.
- **Developer Experience:** You get full IDE autocomplete for the incoming JSON payload (e.g., typing `todo_request.title` will autocomplete).

## 2. How it Works Behind the Scenes
Since Pydantic v2, the core validation engine is written in **Rust** (called `pydantic-core`). This makes it incredibly fast.
1. The client sends a raw JSON string to FastAPI.
2. FastAPI passes the JSON string to Pydantic.
3. Pydantic parses the JSON into a Python dictionary.
4. It iterates over the dictionary, checking every key-value pair against the type hints and constraints defined in your `BaseModel`.
5. If a rule is broken, it immediately stops and generates a detailed HTTP 422 Unprocessable Entity error outlining exactly what field failed and why.
6. If it passes, it instantiates your Pydantic Class and passes that Python object into your endpoint function.

---

## 3. Usage in the Current Project

In `todos.py`, we have the `TodoRequest` model:

```python
from pydantic import BaseModel, Field

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool
```

**What this enforces:**
- `title` must be a string, and it cannot be shorter than 3 characters (e.g., "Hi" fails, "Buy" passes).
- `priority` must be an integer strictly greater than 0 (`gt=0`) and less than 6 (`lt=6`). So, only numbers 1 through 5 are valid priorities.
- `complete` must be a boolean (`True` or `False`).

When used in the route:
```python
@router.post('/todo')
async def create_todo(todo_request: TodoRequest, ...):
    print(todo_request.title) # Safely accessible!
```

---

## 4. Advanced Data Models (Some common Examples)

As your application grows, your schemas will become far more complex. Here are 3 advanced implementations.

### Example A: Nested Models and Complex Types
**The Concept:** A user wants to create a "Company" profile, but a company has multiple physical addresses and a list of specific "tags". We don't want a flat structure; we want a nested JSON payload.

**The Implementation:**
```python
from pydantic import BaseModel, ConfigDict, HttpUrl
from typing import List

class Address(BaseModel):
    street: str
    city: str
    zipcode: str = Field(pattern=r"^\d{5}(-\d{4})?$")  # Regex for US Zipcode

class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    website: HttpUrl  # Validates it starts with http:// or https://
    tags: List[str] = Field(max_length=10) # Max 10 tags allowed
    headquarters: Address # Nested Pydantic Model!
```
**Explanation:** Pydantic recursively validates nested structures. It will first validate the main body, ensure `website` is a valid URL, and then dive into the `headquarters` dictionary to ensure the `Address` rules (like the Regex zip code pattern) are strictly followed.

### Example B: Custom Validators (Domain Logic)
**The Concept:** You are creating a password reset schema. Pydantic's built-in `min_length` isn't enough; you need to ensure the password contains a number, a special character, and doesn't contain the word "password".

**The Implementation:**
```python
from pydantic import BaseModel, field_validator
import re

class PasswordReset(BaseModel):
    new_password: str
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password_complexity(cls, value: str):
        if "password" in value.lower():
            raise ValueError("Password cannot contain the word 'password'")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*]", value):
            raise ValueError("Password must contain a special character")
        return value
```
**Explanation:** The `@field_validator` decorator allows you to write raw Python code to handle custom business logic validation. If your custom function raises a `ValueError`, Pydantic catches it and returns the custom error string gracefully inside the 422 HTTP response to the client.

### Example C: Cross-Field Validation (Model Validators)
**The Concept:** You have a booking system. The user provides a `start_date` and an `end_date`. A `start_date` is perfectly valid on its own, and an `end_date` is perfectly valid on its own. However, the `end_date` *must* occur strictly after the `start_date`.

**The Implementation:**
```python
from pydantic import BaseModel, model_validator
from datetime import date

class HotelBooking(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def check_date_order(self):
        # 'self' contains the fully parsed start_date and end_date objects
        if self.end_date <= self.start_date:
            raise ValueError("Check-out date must be strictly after the check-in date.")
        return self
```
**Explanation:** The `@model_validator(mode='after')` decorator runs *after* all individual fields are verified. It gives you access to the entire object (`self`), allowing you to compare two different fields against each other before the API endpoint is allowed to execute.
