from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware

import models
from database import engine
from routers import auth, todos, admin, users

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creates the database and the table
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
