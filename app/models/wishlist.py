# app/models/wishlist.py
import datetime
from flask import current_app

class WishlistItem:
    def __init__(self, id, uid, pid, time_added):
        self.id = id
        self.uid = uid
        self.pid = pid
        self.time_added = time_added

    @classmethod
    def from_row(cls, row):
        # Handle dict-like rows or tuple rows returned by your DB wrapper.
        if row is None:
            return None
        try:
            # prefer dict-style
            return cls(row['id'], row['uid'], row['pid'], row['time_added'])
        except Exception:
            # fallback to tuple indexing
            return cls(row[0], row[1], row[2], row[3])

    @classmethod
    def get_for_user(cls, uid):
        sql = """
            SELECT id, uid, pid, time_added
            FROM Wishes
            WHERE uid = %s
            ORDER BY time_added DESC
        """
        cur = current_app.db.execute(sql, (uid,))
        rows = cur.fetchall()
        return [cls.from_row(r) for r in rows]

    @classmethod
    def add(cls, uid, pid, time_added=None):
        if time_added is None:
            time_added = datetime.datetime.utcnow()
        sql = """
            INSERT INTO Wishes (uid, pid, time_added)
            VALUES (%s, %s, %s)
            RETURNING id, uid, pid, time_added
        """
        cur = current_app.db.execute(sql, (uid, pid, time_added))
        row = cur.fetchone()
        return cls.from_row(row)

    @classmethod
    def exists(cls, uid, pid):
        sql = "SELECT COUNT(*) FROM Wishes WHERE uid = %s AND pid = %s"
        cur = current_app.db.execute(sql, (uid, pid))
        count = cur.fetchone()[0]
        return count > 0
