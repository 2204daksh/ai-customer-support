from app.repo import repository as repo


def list_events() -> list[dict]:
    return repo.list_events()


def list_tickets() -> list[dict]:
    return repo.list_tickets()


def list_messages(ticket_id: int) -> list[dict]:
    return repo.list_messages(ticket_id)
