# backend/retention.py
import os
import argparse
import datetime as dt
from urllib.parse import urlparse

from backend.db import get_connection
from backend.config import MEDIA_ROOT, MEDIA_BASE_URL

BATCH_SIZE = 1000
DEFAULT_DAYS = 35  # retention window


def _safe_abspath_from_url(url: str) -> str | None:
    if not url:
        return None
    try:
        if url.startswith(MEDIA_BASE_URL):
            rel = url[len(MEDIA_BASE_URL):].lstrip("/\\")
        else:
            path = urlparse(url).path  # e.g., /media/screenshots/abc.png
            rel = path.lstrip("/\\")
            if rel.startswith("media/"):
                rel = rel[len("media/"):]
        abspath = os.path.abspath(os.path.join(MEDIA_ROOT, rel))
        media_root_abs = os.path.abspath(MEDIA_ROOT)
        if not abspath.startswith(media_root_abs + os.sep) and abspath != media_root_abs:
            return None
        return abspath
    except Exception:
        return None


def _delete_files(paths: list[str]) -> int:
    deleted = 0
    for p in paths:
        try:
            if p and os.path.isfile(p):
                os.remove(p)
                deleted += 1
        except Exception:
            pass
    return deleted


def _select_ids_where_older(table: str, ts_col: str, cutoff, id_col: str = "id"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {ts_col} < %s", (cutoff,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[id_col] for r in rows]


def _delete_by_ids(table: str, ids: list[int], id_col: str = "id") -> int:
    if not ids:
        return 0
    conn = get_connection()
    cur = conn.cursor()
    total = 0
    for i in range(0, len(ids), BATCH_SIZE):
        batch = ids[i:i+BATCH_SIZE]
        placeholders = ",".join(["%s"] * len(batch))
        cur.execute(f"DELETE FROM {table} WHERE {id_col} IN ({placeholders})", batch)
        total += cur.rowcount or 0
    cur.close()
    conn.close()
    return total


def _collect_media_urls(table: str, ts_col: str, cutoff) -> list[tuple[int, str]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"""SELECT id, url FROM {table}
            WHERE {ts_col} < %s AND url IS NOT NULL AND url <> ''""",
        (cutoff,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [(r["id"], r["url"]) for r in rows]


def purge_old_data(days: int = DEFAULT_DAYS, dry_run: bool = False) -> None:
    now = dt.datetime.utcnow()
    cutoff_dt = now - dt.timedelta(days=days)       # for TIMESTAMP columns
    cutoff_date = (now - dt.timedelta(days=days)).date()  # for DATE columns

    print(f"[Retention] Purging items older than {days} days…")

    # 1) screenshots (files + rows)
    scr_rows = _collect_media_urls("screenshots", "taken_at", cutoff_dt)
    scr_paths = [_safe_abspath_from_url(u) for (_id, u) in scr_rows]
    scr_ids = [i for (i, _u) in scr_rows]
    if dry_run:
        print(f"[screenshots] would delete rows: {len(scr_ids)}; files: {sum(1 for p in scr_paths if p and os.path.isfile(p))}")
    else:
        deleted_files = _delete_files([p for p in scr_paths if p])
        deleted_rows = _delete_by_ids("screenshots", scr_ids)
        print(f"[screenshots] deleted rows: {deleted_rows}; files: {deleted_files}")

    # 2) screen_recordings (files + rows)
    rec_rows = _collect_media_urls("screen_recordings", "recorded_at", cutoff_dt)
    rec_paths = [_safe_abspath_from_url(u) for (_id, u) in rec_rows]
    rec_ids = [i for (i, _u) in rec_rows]
    if dry_run:
        print(f"[screen_recordings] would delete rows: {len(rec_ids)}; files: {sum(1 for p in rec_paths if p and os.path.isfile(p))}")
    else:
        deleted_files = _delete_files([p for p in rec_paths if p])
        deleted_rows = _delete_by_ids("screen_recordings", rec_ids)
        print(f"[screen_recordings] deleted rows: {deleted_rows}; files: {deleted_files}")

    # 3) activity_events
    ev_ids = _select_ids_where_older("activity_events", "occurred_at", cutoff_dt)
    if dry_run:
        print(f"[activity_events] would delete rows: {len(ev_ids)}")
    else:
        deleted_rows = _delete_by_ids("activity_events", ev_ids)
        print(f"[activity_events] deleted rows: {deleted_rows}")

    # 4) user_overtimes (DATE)
    ot_ids = _select_ids_where_older("user_overtimes", "ot_date", cutoff_date)
    if dry_run:
        print(f"[user_overtimes] would delete rows: {len(ot_ids)}")
    else:
        deleted_rows = _delete_by_ids("user_overtimes", ot_ids)
        print(f"[user_overtimes] deleted rows: {deleted_rows}")

    print("[Retention] Done.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS, help="Items older than this many days are purged")
    ap.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = ap.parse_args()
    purge_old_data(days=args.days, dry_run=args.dry_run)
