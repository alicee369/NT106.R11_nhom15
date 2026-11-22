from __future__ import annotations

from Models import notes
from sqlmodel import Session, select


# UC8: Xem danh sách ghi chú
def get_notes(db: Session, user_id: int) -> list[notes]:
    statement = (
        select(notes).where(notes.user_id == user_id).order_by(notes.updated_at.desc())
    )
    user_notes = db.exec(statement).all()
    return list(user_notes)


# UC9: Thêm ghi chú
def create_note(
    db: Session, user_id: int, title: str, content: str, is_todo: bool = False
) -> notes:
    title = title.strip()
    content = content.strip()
    if not content:
        raise ValueError("Nội dung ghi chú không được để trống.")

    # Nếu tiêu đề rỗng, lấy một phần nội dung làm tiêu đề tạm
    if not title:
        title = (content[:30] + "...") if len(content) > 30 else content

    note = notes(
        user_id=user_id,
        title=title,
        content=content,
        is_todo=is_todo,
        is_completed=False,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# UC10: Sửa ghi chú (Sửa nội dung hoặc tick hoàn thành todo)
def update_note(
    db: Session,
    user_id: int,
    note_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    is_todo: bool | None = None,
    is_completed: bool | None = None,
) -> notes:

    note = db.get(notes, note_id)
    if not note or note.user_id != user_id:
        raise ValueError("Không tìm thấy ghi chú hoặc bạn không có quyền sửa.")

    if title is not None:
        note.title = title.strip()

    if content is not None:
        content = content.strip()
        if not content:
            # Như đặc tả UC10 luồng 2a: nếu xóa trắng -> chuyển thành xóa ghi chú
            delete_note(db, user_id, note_id)
            raise ValueError("Nội dung trống, ghi chú đã tự động bị xóa.")
        note.content = content

    if is_todo is not None:
        note.is_todo = is_todo
    if is_completed is not None:
        note.is_completed = is_completed

    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# UC11: Xóa ghi chú
def delete_note(db: Session, user_id: int, note_id: int) -> bool:
    note = db.get(notes, note_id)
    if not note or note.user_id != user_id:
        raise ValueError("Không tìm thấy ghi chú hoặc bạn không có quyền xóa.")

    db.delete(note)
    db.commit()
    return True
