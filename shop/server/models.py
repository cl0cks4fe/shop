from datetime import datetime, timedelta
from extensions import db


class Device(db.Model):
    id = db.Column(db.String, primary_key=True)
    url = db.Column(db.String)
    last_seen = db.Column(db.String)

    @property
    def connected(self):
        if not self.last_seen:
            return False
        try:
            last_seen_dt = datetime.fromisoformat(self.last_seen)
        except Exception:
            return False
        return (datetime.now() - last_seen_dt) <= timedelta(minutes=1)
