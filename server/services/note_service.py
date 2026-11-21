import math
from typing import Dict, Optional
from sqlmodel import Session

_notes: Dict[int, dict] = {}
_next_note_id = 1


def list_notes(session: Session, user_id: int, page: int, limit: int) -> dict:
    user_notes = [n for n in _notes.values() if n["user_id"] == user_id]
    user_notes.sort(key=lambda item: item["note_id"], reverse=True)

    total_count = len(user_notes)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    offset = (page - 1) * limit
    sliced = user_notes[offset : offset + limit]

    return {
        "notes": [
            {
                "noteId": n["note_id"],
                "title": n["title"],
                "content": n["content"],
                "isTodoList": n["is_todo_list"],
                "isDone": n["is_done"],
            }
            for n in sliced
        ],
        "totalCount": total_count,
        "totalPages": total_pages,
    }


def create_note(
    session: Session,
    user_id: int,
    title: str,
    content: str,
    is_todo_list: bool,
) -> dict:
    global _next_note_id
    record = {
        "note_id": _next_note_id,
        "user_id": user_id,
        "title": title.strip(),
        "content": content,
        "is_todo_list": is_todo_list,
        "is_done": False,
    }
    _notes[_next_note_id] = record
    _next_note_id += 1
    return record


def get_note(session: Session, user_id: int, note_id: int) -> Optional[dict]:
    record = _notes.get(note_id)
    if not record or record["user_id"] != user_id:
        return None
    return record


def update_note(
    session: Session,
    user_id: int,
    note_id: int,
    title: str,
    content: str,
    is_todo_list: bool,
    is_done: bool,
) -> Optional[dict]:
    record = get_note(session, user_id, note_id)
    if not record:
        return None

    record["title"] = title.strip()
    record["content"] = content
    record["is_todo_list"] = is_todo_list
    record["is_done"] = is_done
    return record


def delete_note(session: Session, user_id: int, note_id: int) -> bool:
    record = get_note(session, user_id, note_id)
    if not record:
        return False
    del _notes[note_id]
    return True