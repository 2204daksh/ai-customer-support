from app.repo import repository as db


def list_knowledge_base() -> list[dict]:
    return db.list_knowledge_base()


def update_knowledge_base_entry(entry_id: int, title: str, content: str) -> dict | None:
    return db.update_knowledge_base_entry(entry_id, title, content)
