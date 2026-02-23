# 1. Start with a lightweight Linux image
FROM python:3.12-slim

# 2. Copy the pre-built 'uv' program directly from the creators
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set the working directory
WORKDIR /todoapp

# 4. Copy your project files into the container
COPY . /todoapp

# 5. Use uv to install your app and its dependencies from pyproject.toml
RUN uv pip install --system .

# 6. Start the FastAPI server (assuming your main file is main.py and app instance is app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]