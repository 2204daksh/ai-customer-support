from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.service import auth, knowledge_service, metric_service, poll_service, ticket_service

api = APIRouter(prefix="/api", dependencies=[Depends(auth.require_login)])


class EntryUpdate(BaseModel):
    title: str
    content: str


@api.get("/login")
def login() -> dict:
    return {"ok": True}


@api.get("/events")
def events() -> list[dict]:
    return ticket_service.list_events()


@api.get("/tickets")
def tickets() -> list[dict]:
    return ticket_service.list_tickets()


@api.get("/tickets/{ticket_id}/messages")
def ticket_messages(ticket_id: int) -> list[dict]:
    return ticket_service.list_messages(ticket_id)


@api.get("/knowledge-base")
def knowledge_base() -> list[dict]:
    return knowledge_service.list_knowledge_base()


@api.put("/knowledge-base/{entry_id}")
def update_entry(entry_id: int, update: EntryUpdate) -> dict:
    entry = knowledge_service.update_knowledge_base_entry(entry_id, update.title, update.content)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@api.post("/poll")
def poll() -> dict:
    return poll_service.run_poll()


@api.get("/metrics")
def metrics() -> dict:
    return metric_service.get_metrics()
