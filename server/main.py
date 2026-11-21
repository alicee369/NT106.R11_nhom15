from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dependencies import AuthError
from routers import auth, note, pomodoro, profile, reminder, schedule

# Khởi tạo Server
app = FastAPI(title="app quản lí học tập API - NT106")

app.add_middleware(
    CORSMiddleware,# type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    action, request_id = "UNKNOWN", 0
    try:
        body = await request.json()
        if isinstance(body, dict):
            action = body.get("action", "UNKNOWN")
            request_id = body.get("requestId", 0)
    except (ValueError, RuntimeError):
        pass

    return JSONResponse(
        status_code=401,
        content={
            "action": action,
            "requestId": request_id,
            "success": False,
            "errorCode": exc.error_code,
            "message": exc.message,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    action, request_id = "UNKNOWN", 0
    if isinstance(exc.body, dict):
        action = exc.body.get("action", "UNKNOWN")
        request_id = exc.body.get("requestId", 0)

    return JSONResponse(
        status_code=422,
        content={
            "action": action,
            "requestId": request_id,
            "success": False,
            "errorCode": "INVALID_REQUEST_DATA",
            "message": "Dữ liệu gửi lên không đúng định dạng quy ước.",
            "data": None,
        },
    )


# Gộp API cũ: Auth & Profile (UC22-UC27)
app.include_router(auth.router)
app.include_router(profile.router)

# Gộp API mới: Pomodoro, Schedule, Note, Reminder (UC1-UC12)
app.include_router(pomodoro.router)
app.include_router(schedule.router)
app.include_router(note.router)
app.include_router(reminder.router)

# Chạy server: uvicorn main:app --reload