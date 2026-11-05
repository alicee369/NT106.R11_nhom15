from fastapi import FastAPI
from routers import auth, profile
from fastapi.middleware.cors import CORSMiddleware
# Khởi tạo Server
app = FastAPI(title="app quản lí học tập API - NT106")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gộp API: Auth & Profile
app.include_router(auth.router)
app.include_router(profile.router)

# Chạy server: uvicorn main:app --reload