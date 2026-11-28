from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dependencies import AuthError
from routers import (
    auth,
    note,
    plan,
    pomodoro,
    profile,
    reminder,
    schedule,
    score,
    statistic,
)

# Khởi tạo Server
app = FastAPI(title="app quản lí học tập API - NT106")

app.add_middleware(
    CORSMiddleware,  # type: ignore
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
            action = body.get("action") or "UNKNOWN"
            request_id = body.get("requestId") or 0
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
async def validation_error_handler(request: Request, exc: RequestValidationError):
    action, request_id = "UNKNOWN", 0
    if isinstance(exc.body, dict):
        action = exc.body.get("action") or "UNKNOWN"
        request_id = exc.body.get("requestId") or 0

    path = request.url.path.rstrip("/")

    if path.endswith("/api/score/estimate"):
        return JSONResponse(
            status_code=400,
            content={
                "action": "SCORE_ESTIMATE_GPA",
                "requestId": request_id,
                "success": False,
                "errorCode": "SCORE_TARGET_UNACHIEVABLE",
                "message": "Mục tiêu không khả thi hoặc định dạng sai.",
                "data": None,
            },
        )
    if path.endswith("/api/plan/create"):
        return JSONResponse(
            status_code=400,
            content={
                "action": "PLAN_CREATE",
                "requestId": request_id,
                "success": False,
                "errorCode": "PLAN_EMPTY_INFO",
                "message": "Thông tin không được để trống.",
                "data": None,
            },
        )
    if path.endswith("/api/plan/update"):
        return JSONResponse(
            status_code=400,
            content={
                "action": "PLAN_UPDATE",
                "requestId": request_id,
                "success": False,
                "errorCode": "PLAN_NOT_FOUND",
                "message": "Thông tin trống hoặc không tìm thấy kế hoạch.",
                "data": None,
            },
        )
    if path.endswith("/api/plan/delete"):
        return JSONResponse(
            status_code=400,
            content={
                "action": "PLAN_DELETE",
                "requestId": request_id,
                "success": False,
                "errorCode": "PLAN_NOT_FOUND",
                "message": "Không tìm thấy kế hoạch.",
                "data": None,
            },
        )

    # Giữ nguyên chuẩn cũ cho Auth, Profile và UC1-UC12
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

# Gộp API Cụm 1: Pomodoro, Schedule, Note, Reminder (UC1-UC12)
app.include_router(pomodoro.router)
app.include_router(schedule.router)
app.include_router(note.router)
app.include_router(reminder.router)

# Gộp API Cụm 2: Study Plan, Statistic, Score & GPA (UC13-UC16, UC18)
app.include_router(plan.router)
app.include_router(statistic.router)
app.include_router(score.router)
# Chạy server: uvicorn main:app --reload 