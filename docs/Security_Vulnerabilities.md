# Application Security Vulnerabilities

While this `project-3` codebase serves as an excellent foundation for learning FastAPI, there are several "learning shortcuts" taken that would be considered critical security vulnerabilities if deployed to a production environment. 

Here is a scan of the current security issues present in the app, ranked by severity, along with how to fix them.

---

## 🛑 Critical Severity (Fix Before Deployment)

### 1. Hardcoded Cryptographic Secrets
**File:** `todoapp/routers/auth.py`
```python
SECRET_KEY = '8c911fe68d0ffaa34dac689122b38127655d76ccd7c5e33648cd92bf51add5ef'
```
- **The Threat:** The `SECRET_KEY` is literally the master key to your kingdom. If an attacker gains read-access to your codebase (e.g., you make the GitHub repo public), they can use this string to mint perfectly valid JSON Web Tokens (JWT) for *any* user, including the root "admin," without ever needing a password.
- **The Fix:** Never hardcode secrets in source code. Load them dynamically using environment variables (`os.getenv("SECRET_KEY")`) and store the actual key in a strictly ignored `.env` file or a secure Secret Manager (like AWS Systems Manager or Docker Secrets).

### 2. Hardcoded Database Credentials
**File:** `todoapp/database.py`
```python
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres:test1234@localhost/TodoApplicationDatabase'
```
- **The Threat:** Similar to the `SECRET_KEY`, this exposes the raw database username (`postgres`) and password (`test1234`) to anyone who reads the source code.
- **The Fix:** Move this entire string into an environment variable (`os.getenv("DATABASE_URL")`).

---

## ⚠️ High Severity (Fix Quickly)

### 3. Missing CORS Middleware
**File:** `todoapp/main.py`
- **The Threat:** Currently, there is no Cross-Origin Resource Sharing (CORS) middleware configured. If you deploy a frontend (e.g., a React app at `https://my-frontend.com`) and try to fetch data from this FastAPI backend (`https://api.my-backend.com`), modern browsers will block the request natively. Conversely, without strict CORS rules, *any* malicious website can make requests to your API pretending to be your user.
- **The Fix:** Import and configure `CORSMiddleware` in `main.py`, tightly specifying exactly which frontend URLs are allowed to talk to your backend.

### 4. Weak Password Policies
**File:** `todoapp/routers/auth.py`
```python
class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
```
- **The Threat:** The `CreateUserRequest` uses a raw `str` for the password with zero Pydantic validation. A user could literally register with a 1-character password (e.g., "a"), making brute-force dictionary attacks trivial.
- **The Fix:** Use advanced Pydantic data validation (as detailed in `docs/Pydantic_and_Data_Validation.md`) to enforce `min_length=8` and require at least one number and one special character via Regex validators.

---

## 🟡 Medium Severity (Best Practices)

### 5. No Rate Limiting (DDoS Vulnerability)
**File:** `todoapp/routers/auth.py` 
- **The Threat:** An attacker can execute a script to send 10,000 login requests to `/auth/token` per second. Because password hashing (`bcrypt`) is intentionally computationally expensive, this will instantly spike your server's CPU to 100% and crash the app for genuine users (a Denial of Service attack).
- **The Fix:** Implement a Rate Limiting middleware (such as `slowapi`) to restrict users to a reasonable number of requests (e.g., 5 attempts per minute per IP address on the `/auth/token` route).

### 6. Leaking Server Errors (HTTP 500)
**File:** Project-wide
- **The Threat:** If a database query fails or a bug triggers an unhandled Python exception, FastAPI natively returns a rigid "Internal Server Error" but might leak stack traces depending on the deployment configuration.
- **The Fix:** Implement custom Exception Handlers globally in `main.py` to catch all unhandled exceptions, log them securely to a private monitoring service (like Sentry), and return a sanitized, polite error to the client that reveals no underlying infrastructure details.

### 7. Missing HTTPS Enforcements
**File:** Deployment Context
- **The Threat:** If a user logs into your deployed app over standard HTTP, their plaintext password and their JWT token are sent across the open internet unencrypted. Anyone sipping the Wi-Fi traffic at Starbucks can steal the token and impersonate them immediately.
- **The Fix:** Ensure the hosting provider (Render, DigitalOcean, etc.) enforces strict TLS/SSL (HTTPS) termination, and configure FastAPI to reject non-HTTPS requests or redirect them.
