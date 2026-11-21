from typing import List, Optional
from pydantic import BaseModel


# --- UC1 ---
class PomodoroStartData(BaseModel):
    planId: Optional[int] = None
    focusMinutes: int
    breakMinutes: int


class PomodoroSessionIdData(BaseModel):
    sessionId: int


class BadgeItem(BaseModel):
    badgeId: int
    badgeName: str
    iconUrl: str
    description: str
    isUnlocked: bool


class PomodoroStartResponseData(BaseModel):
    sessionId: int
    startTime: str


class PomodoroResumeResponseData(BaseModel):
    status: str
    accumulatedSeconds: int


class PomodoroStopResponseData(BaseModel):
    plannedDurationSeconds: int
    actualDurationSeconds: int
    endTime: str
    newlyUnlockedBadges: List[BadgeItem]


# --- UC2 ---
class PomodoroSettingsData(BaseModel):
    focusMinutes: int
    breakMinutes: int


# --- UC3 ---
class MiniPlayerPreferenceData(BaseModel):
    isMiniPlayer: bool