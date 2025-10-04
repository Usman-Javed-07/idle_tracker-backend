from backend.models import update_user_status, record_event


def set_user_status(user_id: int, status: str, active_duration_seconds=None):
    """
    status in {'shift_start','active','inactive'}
    For 'inactive' we also store 'active_duration_seconds' (how long the user had been active).
    NOTE: We now also allow recording an 'active' event with active_duration_seconds representing
    the length of the *inactive* streak that just ended. This keeps a symmetric log so the admin
    app can sum true Active and Inactive time.
    """
    if status not in {"shift_start", "active", "inactive"}:
        raise ValueError("Invalid status")
    update_user_status(user_id, status)
    record_event(user_id, status,
                 active_duration_seconds=active_duration_seconds)
