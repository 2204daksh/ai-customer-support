from app.repo import repository as repo


def list_knowledge_base() -> list[dict]:
    return repo.list_knowledge_base()


def update_knowledge_base_entry(entry_id: int, title: str, content: str) -> dict | None:
    return repo.update_knowledge_base_entry(entry_id, title, content)
