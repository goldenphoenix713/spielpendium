from dataclasses import dataclass
from threading import Lock


@dataclass
class SyncStatus:
    active: bool = False
    current: int = 0
    total: int = 0
    message: str = ""


_status = SyncStatus()
_lock = Lock()


def set_sync_status(
    active: bool, current: int = 0, total: int = 0, message: str = ""
) -> None:
    """Set the sync status.

    Args:
        active: Whether the sync is active.
        current: The current progress of the sync.
        total: The total progress of the sync.
        message: The message to display.
    """
    with _lock:
        _status.active = active
        _status.current = current
        _status.total = total
        _status.message = message


def get_sync_status() -> SyncStatus:
    """Get the sync status.

    Returns:
        SyncStatus: The sync status.
    """
    with _lock:
        return SyncStatus(
            active=_status.active,
            current=_status.current,
            total=_status.total,
            message=_status.message,
        )
