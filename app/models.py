from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime, UTC
from . import db
from . import lm
import json

local_data_filepath = "data.json"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now(UTC))
    last_login = db.Column(db.String(200))
    permissions = db.Column(db.String(4), default="1")
    post_Saved = db.Column(db.Integer, default=0)
    post_owned = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<User %r>" % self.username


class Guest(AnonymousUserMixin):
    def __init__(self):
        self.username = "Guest"
        self.date_created = datetime.now(UTC)
        self.last_login = "N/A"
        self.permissions = "0"


lm.anonymous_user = Guest


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=False)
    desc = db.Column(db.String(5000))
    file_name = db.Column(db.String(1000), nullable=False)
    file_loc = db.Column(db.String(2000), nullable=False)
    author = db.Column(db.String(32), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now(UTC))
    file_type = db.Column(db.String(30), nullable=False)
    saves = db.Column(db.Integer, default=0)
    saved_by = db.Column(db.String(3000), default="[]")
    lowest_view_permission = db.Column(db.String(4), default="1")

    def __repr__(self):
        return f"<Post {self.title} {self.desc}>"


def updateData(key, value):
    with open(local_data_filepath, "r+") as f:
        data = json.load(f)
        data[key] = value
    with open(local_data_filepath, "w") as f:
        json.dump(data, f, indent=4)


# user
# mod
# adm
# su
