from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from sqlmodel import Session as SQLModelSession


@dataclass
class SyncStatus:
    active: bool = False
    current: int = 0
    total: int = 0
    message: str = ""


def set_sync_status(
    username: str,
    active: bool,
    current: int = 0,
    total: int = 0,
    message: str = "",
) -> None:
    """Set the sync status in the database.

    Args:
        username: BGG username of the user whose sync status is being set.
        active: Whether the sync is active.
        current: The current progress of the sync.
        total: The total progress of the sync.
        message: The message to display.
    """
    from util.models import SyncState, engine

    try:
        with SQLModelSession(engine) as session:
            state = session.get(SyncState, username)
            if not state:
                state = SyncState(username=username)
                session.add(state)
            state.active = active
            state.current = current
            state.total = total
            state.message = message
            session.commit()
    except Exception as e:
        logger.error(f"Error setting sync status for {username}: {e}")


def get_sync_status(username: str) -> SyncStatus:
    """Get the sync status for the user from the database.

    Args:
        username: BGG username of the user whose sync status is being fetched.

    Returns:
        SyncStatus: The sync status.
    """
    from util.models import SyncState, engine

    try:
        with SQLModelSession(engine) as session:
            state = session.get(SyncState, username)
            if state:
                return SyncStatus(
                    active=state.active,
                    current=state.current,
                    total=state.total,
                    message=state.message,
                )
    except Exception as e:
        logger.error(f"Error getting sync status for {username}: {e}")

    return SyncStatus(active=False, current=0, total=0, message="")
