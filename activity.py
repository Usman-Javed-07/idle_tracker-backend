from backend.models import record_event

def set_user_status(user_id: int, is_active: bool):
    record_event(user_id, "active" if is_active else "inactive")
