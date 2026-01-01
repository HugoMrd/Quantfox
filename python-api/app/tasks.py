from datetime import date

from app.celery_app import celery_app
from app.database import compute_daily_averages


@celery_app.task(bind=True, name="compute_daily_averages")
def compute_daily_averages_task(self, start_date_str: str, end_date_str: str) -> list[dict]:
    """
    Celery task to compute daily average prices.
    Delegates the actual computation to the database module.
    """
    start_date = date.fromisoformat(start_date_str)
    end_date = date.fromisoformat(end_date_str)

    return compute_daily_averages(start_date, end_date)
