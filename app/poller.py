import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import settings
from app.clients.gmail import Gmail
from app.core.logger import setup_logging
from app.services.pipeline import handle_message

setup_logging(level=logging.INFO)

# Limit concurrent worker threads so LLM calls don't all fire at once.
MAX_CONCURRENT_WORKERS = 2

# Stagger message submissions so LLM calls are spread out over time instead of all hitting the API in the first second.
SUBMIT_DELAY_SECONDS = 2.0


def poll_once() -> int:
    gmail = Gmail()
    message_ids = gmail.list_new_message_ids()

    # Submit every message to a worker thread with a small delay between
    # submissions so LLM calls are spaced out and don't exceed the API rate limit.
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_WORKERS) as thread_pool:
        submitted_tasks = []
        for message_id in message_ids:
            submitted_task = thread_pool.submit(handle_message, gmail, message_id)
            submitted_tasks.append(submitted_task)
            time.sleep(SUBMIT_DELAY_SECONDS)

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
