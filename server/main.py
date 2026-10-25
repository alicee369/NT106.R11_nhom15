from fastapi import FastAPI
from routers import auth, profile

# Khởi tạo Server
app = FastAPI(title="app quản lí học tập API - NT106")

# Gộp API: Auth & Profile
app.include_router(auth.router)
app.include_router(profile.router)

# Chạy server: uvicorn main:app --reload