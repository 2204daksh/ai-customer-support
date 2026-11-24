import atexit
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.core.config import settings

# One shared pool instead of a new TCP connection per DB call.
pool = ConnectionPool(
    conninfo=settings.database_url,
    min_size=1,
    max_size=20,
    open=True,
    kwargs={"row_factory": dict_row},
)

# Ensure the pool (and its worker threads) shut down cleanly on process exit.
atexit.register(pool.close)


@contextmanager
def connect():
    """Yield a pooled connection."""
    with pool.connection() as conn:
        yield conn
