import math
from typing import Optional

from CRUD import note as note_crud
from Models import notes
from sqlmodel import Session


def _model_to_internal_dict(n: notes) -> dict:
    return {
        "note_id": n.id,
        "user_id": n.user_id,
        "title": n.title,
        "content": n.content,
        "is_todo_list": n.is_todo,
        "is_done": n.is_completed,
    }


def list_notes(session: Session, user_id: int, page: int, limit: int) -> dict:
    user_notes = note_crud.get_notes(session, user_id)

    total_count = len(user_notes)
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    offset = (page - 1) * limit
    sliced = user_notes[offset : offset + limit]

    return {
        "notes": [
            {
                "noteId": n.id,
                "title": n.title,
                "content": n.content,
                "isTodoList": n.is_todo,
                "isDone": n.is_completed,
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
    n = note_crud.create_note(
        db=session,
        user_id=user_id,
        title=title,
        content=content,
        is_todo=is_todo_list,
    )
    return _model_to_internal_dict(n)


def get_note(session: Session, user_id: int, note_id: int) -> Optional[dict]:
    n = session.get(notes, note_id)
    if not n or n.user_id != user_id:
        return None
    return _model_to_internal_dict(n)


def update_note(
    session: Session,
    user_id: int,
    note_id: int,
    title: str,
    content: str,
    is_todo_list: bool,
    is_done: bool,
) -> Optional[dict]:
    try:
        n = note_crud.update_note(
            db=session,
            user_id=user_id,
            note_id=note_id,
            title=title,
            content=content,
            is_todo=is_todo_list,
            is_completed=is_done,
        )
    except ValueError:
        return None
    return _model_to_internal_dict(n)


def delete_note(session: Session, user_id: int, note_id: int) -> bool:
    try:
        return note_crud.delete_note(
            db=session,
            user_id=user_id,
            note_id=note_id,
        )
    except ValueError:
        return False
