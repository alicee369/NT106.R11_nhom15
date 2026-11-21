from fastapi import APIRouter, Depends
from sqlmodel import Session

from database import get_session
from dependencies import get_current_user_id
from schemas.base import BaseRequest, BaseResponse
from schemas.note import (
    NoteAddData,
    NoteDeleteData,
    NoteListData,
    NoteListResponseData,
    NoteUpdateData,
    NoteUpdateResponseData,
)
from services import note_service

router = APIRouter(prefix="/api/note", tags=["Note (UC8 - UC11)"])


@router.post("/list", response_model=BaseResponse[NoteListResponseData])
async def list_notes(
    req: BaseRequest[NoteListData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    page = max(1, req.data.page)
    limit = max(1, req.data.limit)

    result = note_service.list_notes(session, user_id, page, limit)
    return BaseResponse(
        action="NOTE_GET_LIST",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Thành công.",
        data=NoteListResponseData(**result),
    )


@router.post("/add", response_model=BaseResponse[None])
async def add_note(
    req: BaseRequest[NoteAddData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    if not req.data.content.strip():
        return BaseResponse(
            action="NOTE_ADD",
            requestId=req.requestId,
            success=False,
            errorCode="NOTE_EMPTY_CONTENT",
            message="Nội dung ghi chú rỗng.",
            data=None,
        )

    note_service.create_note(
        session=session,
        user_id=user_id,
        title=req.data.title,
        content=req.data.content,
        is_todo_list=req.data.isTodoList,
    )
    return BaseResponse(
        action="NOTE_ADD",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã thêm ghi chú.",
        data=None,
    )


@router.post("/update", response_model=BaseResponse[NoteUpdateResponseData])
async def update_note(
    req: BaseRequest[NoteUpdateData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    existing = note_service.get_note(session, user_id, req.data.noteId)
    if existing is None:
        return BaseResponse(
            action="NOTE_UPDATE",
            requestId=req.requestId,
            success=False,
            errorCode="NOTE_NOT_FOUND",
            message="Không tìm thấy ghi chú.",
            data=None,
        )

    # Luồng ngoại lệ 2a của UC10: Xóa trắng nội dung -> tự chuyển sang xóa ghi chú
    if not req.data.content.strip():
        note_service.delete_note(session, user_id, req.data.noteId)
        return BaseResponse(
            action="NOTE_UPDATE",
            requestId=req.requestId,
            success=True,
            errorCode=None,
            message="Cập nhật thành công.",
            data=NoteUpdateResponseData(isDeleted=True),
        )

    note_service.update_note(
        session=session,
        user_id=user_id,
        note_id=req.data.noteId,
        title=req.data.title,
        content=req.data.content,
        is_todo_list=req.data.isTodoList,
        is_done=req.data.isDone,
    )
    return BaseResponse(
        action="NOTE_UPDATE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Cập nhật thành công.",
        data=NoteUpdateResponseData(isDeleted=False),
    )


@router.post("/delete", response_model=BaseResponse[None])
async def delete_note(
    req: BaseRequest[NoteDeleteData],
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_session),
):
    deleted = note_service.delete_note(session, user_id, req.data.noteId)
    if not deleted:
        return BaseResponse(
            action="NOTE_DELETE",
            requestId=req.requestId,
            success=False,
            errorCode="NOTE_NOT_FOUND",
            message="Không tìm thấy ghi chú.",
            data=None,
        )

    return BaseResponse(
        action="NOTE_DELETE",
        requestId=req.requestId,
        success=True,
        errorCode=None,
        message="Đã xóa ghi chú.",
        data=None,
    )