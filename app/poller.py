import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import settings
from app.clients.gmail import Gmail
from app.core.logger import setup_logging
from app.services.pipeline import handle_message

setup_logging(level=logging.INFO)


# How many messages are processed at the same time.
# Each message waits on the Gmail API and the database, so threads let us
# overlap those waits instead of doing them one after another.
MAX_CONCURRENT_WORKERS = 5


def poll_once() -> int:
    gmail = Gmail()
    message_ids = gmail.list_new_message_ids()

    # Submit every message to a worker thread so they run concurrently.
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as thread_pool:
        submitted_tasks = []
        for message_id in message_ids:
            submitted_task = thread_pool.submit(handle_message, gmail, message_id)
            submitted_tasks.append(submitted_task)

        # Wait for every thread to finish, errors are surfaced by the decorated
        # DB/LLM calls inside handle_message.
        for submitted_task in as_completed(submitted_tasks):
            try:
                submitted_task.result()
            except Exception:
                pass

    return len(message_ids)


def main() -> None:
    while True:
        try:
            count = poll_once()
        except Exception:
            pass
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()