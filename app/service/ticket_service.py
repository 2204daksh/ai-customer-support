from app.repo import repository as db


def list_events() -> list[dict]:
    return db.list_events()


def list_tickets() -> list[dict]:
    return db.list_tickets()


def list_messages(ticket_id: int) -> list[dict]:
    return db.list_messages(ticket_id)
