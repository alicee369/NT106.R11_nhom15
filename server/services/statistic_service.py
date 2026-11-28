import calendar
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from Models import StudyPlan, pomo_session
from sqlmodel import Session, select

WEEKDAY_LABELS = [
    "Thứ 2",
    "Thứ 3",
    "Thứ 4",
    "Thứ 5",
    "Thứ 6",
    "Thứ 7",
    "Chủ nhật",
]


def _resolve_tz(tz_name: Optional[str]) -> tzinfo:
    name = (tz_name or "Asia/Ho_Chi_Minh").strip()
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        # Dự phòng an toàn trên Windows khi chưa cài gói tzdata
        lower = name.lower()
        if any(k in lower for k in ("ho_chi_minh", "saigon", "bangkok", "vietnam", "+07")):
            return timezone(timedelta(hours=7))
        return timezone.utc


def _to_local(dt: datetime, tz: tzinfo) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)


def get_study_chart(
    session: Session,
    user_id: int,
    filter_type: str,
    timezone_str: str = "Asia/Ho_Chi_Minh",
    subject_tag: Optional[str] = None,
) -> dict:
    tz = _resolve_tz(timezone_str)
    now_local = datetime.now(timezone.utc).astimezone(tz)
    today = now_local.date()

    # Xác định khung thời gian và danh sách cột biểu đồ theo filterType
    if filter_type == "DAY":
        # 7 ngày gần nhất kết thúc ở hôm nay (nhãn YYYY-MM-DD)
        start_date = today - timedelta(days=6)
        end_date = today
        buckets: List[str] = [
            (start_date + timedelta(days=i)).isoformat() for i in range(7)
        ]
    elif filter_type == "WEEK":
        # Tuần hiện tại từ Thứ 2 đến Chủ nhật
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        buckets = list(WEEKDAY_LABELS)
    else:  # "MONTH"
        # Các tuần trong tháng hiện tại
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        start_date = today.replace(day=1)
        end_date = today.replace(day=days_in_month)
        num_weeks = (days_in_month - 1) // 7 + 1
        buckets = [f"Tuần {w}" for w in range(1, num_weeks + 1)]

    # Đọc toàn bộ phiên học và tên kế hoạch của user từ Supabase
    sessions = list(
        session.exec(
            select(pomo_session).where(pomo_session.user_id == user_id)
        ).all()
    )
    if not sessions:
        return {"totalStudyMinutes": 0, "chartData": []}

    plans = session.exec(
        select(StudyPlan).where(StudyPlan.user_id == user_id)
    ).all()
    plan_name_map: Dict[int, str] = {int(p.id): p.name for p in plans if p.id is not None}

    raw_tag = (subject_tag or "").strip()
    is_all_subjects = (not raw_tag) or (raw_tag.lower() in ("tất cả", "all"))
    filter_tag_lower = raw_tag.lower()
    display_tag = "Tổng" if is_all_subjects else raw_tag

    bucket_totals: Dict[str, int] = {label: 0 for label in buckets}
    total_minutes = 0

    for ps in sessions:
        local_dt = _to_local(ps.completed_at, tz)
        local_date = local_dt.date()
        if local_date < start_date or local_date > end_date:
            continue

        session_tag = (
            plan_name_map.get(ps.plan_id, "Tự do")
            if ps.plan_id is not None
            else "Tự do"
        )
        if not is_all_subjects and session_tag.strip().lower() != filter_tag_lower:
            continue

        mins = max(0, int(ps.duration_min))
        if filter_type == "DAY":
            label = local_date.isoformat()
        elif filter_type == "WEEK":
            label = WEEKDAY_LABELS[local_date.weekday()]
        else:
            week_idx = (local_date.day - 1) // 7 + 1
            label = f"Tuần {week_idx}"

        if label in bucket_totals:
            bucket_totals[label] += mins
            total_minutes += mins

    # Empty State chuẩn: không có phút học nào trong khung lọc -> trả mảng rỗng []
    if total_minutes == 0:
        return {"totalStudyMinutes": 0, "chartData": []}

    chart_data = [
        {
            "label": label,
            "subjectTag": display_tag,
            "studyMinutes": bucket_totals[label],
        }
        for label in buckets
    ]
    return {
        "totalStudyMinutes": total_minutes,
        "chartData": chart_data,
    }
