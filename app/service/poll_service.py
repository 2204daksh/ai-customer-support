from app.poller import poll_once


def poll_messages() -> dict:
    return {"messages": poll_once()}
