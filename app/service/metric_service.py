from app.repo import repository as repo


def get_metrics() -> dict:
    return repo.list_metrics()
