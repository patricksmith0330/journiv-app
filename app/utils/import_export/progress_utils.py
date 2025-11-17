"""
Progress callback utilities for import/export operations.
"""
from typing import Callable, Optional
from sqlalchemy.orm import Session


def create_throttled_progress_callback(
    job,
    db: Session,
    max_progress: int = 90,
    commit_interval: int = 10,
    percentage_threshold: int = 5,
) -> Callable[[int, int], None]:
    """
    Create a throttled progress callback that commits to DB efficiently.

    Args:
        job: Job object with processed_items, total_items, and set_progress method
        db: Database session
        max_progress: Maximum progress percentage (default 90, leaving room for finalization)
        commit_interval: Commit every N entries (default 10)
        percentage_threshold: Commit on N% progress changes (default 5)

    Returns:
        Progress callback function
    """
    last_committed_progress = 0
    last_committed_percentage = 0

    def handle_progress(processed: int, total: int):
        nonlocal last_committed_progress, last_committed_percentage
        job.processed_items = processed
        job.total_items = total

        if total > 0:
            progress_percentage = min(max_progress, int((processed / total) * max_progress))
            job.set_progress(progress_percentage)

            should_commit = (
                (processed - last_committed_progress) >= commit_interval or
                (progress_percentage - last_committed_percentage) >= percentage_threshold or
                processed == total
            )

            if should_commit:
                db.commit()
                last_committed_progress = processed
                last_committed_percentage = progress_percentage
        else:
            db.commit()

    return handle_progress

