import psycopg2
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Generator

from app.config import get_config


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    config = get_config()
    conn = psycopg2.connect(config.database.connection_string)
    try:
        yield conn
    finally:
        conn.close()


def compute_daily_averages(start_date: date, end_date: date) -> list[dict]:
    """
    Compute daily average prices using SQL aggregation.
    This is optimized to perform the computation at the database level.
    """
    query = """
        SELECT
            DATE(recorded_at) as date,
            AVG(price) as average_price
        FROM prices
        WHERE DATE(recorded_at) >= %s AND DATE(recorded_at) <= %s
        GROUP BY DATE(recorded_at)
        ORDER BY date
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

    return [
        {
            "date": row[0].isoformat(),
            "average_price": float(round(Decimal(str(row[1])), 2)),
        }
        for row in rows
    ]
