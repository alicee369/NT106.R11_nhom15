from typing import List
from pydantic import BaseModel


class NoteListData(BaseModel):
    page: int
    limit: int


class NoteItem(BaseModel):
    noteId: int
    title: str
    content: str
    isTodoList: bool
    isDone: bool


class NoteListResponseData(BaseModel):
    notes: List[NoteItem]
    totalCount: int
    totalPages: int


class NoteAddData(BaseModel):
    title: str
    content: str
    isTodoList: bool


class NoteUpdateData(BaseModel):
    noteId: int
    title: str
    content: str
    isTodoList: bool
    isDone: bool


class NoteUpdateResponseData(BaseModel):
    isDeleted: bool


class NoteDeleteData(BaseModel):
    noteId: int