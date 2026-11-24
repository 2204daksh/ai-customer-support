from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.service.auth import require_login
from app.service.knowledge_service import list_knowledge_base, update_knowledge_base_entry
from app.service.poll_service import poll_messages
from app.service.ticket_service import list_events, list_messages, list_tickets

api = APIRouter(prefix="/api", dependencies=[Depends(require_login)])


class EntryUpdate(BaseModel):
    title: str
    content: str


@api.get("/login")
def login() -> dict:
    return {"ok": True}


@api.get("/events")
def events() -> list[dict]:
    return list_events()


@api.get("/tickets")
def tickets() -> list[dict]:
    return list_tickets()


@api.get("/tickets/{ticket_id}/messages")
def ticket_messages(ticket_id: int) -> list[dict]:
    return list_messages(ticket_id)


@api.get("/knowledge-base")
def knowledge_base() -> list[dict]:
    return list_knowledge_base()


@api.put("/knowledge-base/{entry_id}")
def update_entry(entry_id: int, update: EntryUpdate) -> dict:
    entry = update_knowledge_base_entry(entry_id, update.title, update.content)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@api.post("/poll")
def poll() -> dict:
    return poll_messages()
