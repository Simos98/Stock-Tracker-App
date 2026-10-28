from datetime import UTC, datetime

from passlib.hash import pbkdf2_sha256 as sha256

from src.extensions import db

MIN_PASSWORD_LENGTH = 8
NOTIFICATION_FREQUENCIES = ("daily", "weekly", "realtime_critical")


def utcnow():
    # Naive UTC, matching the timezone-less DateTime columns (datetime.utcnow is deprecated)
    return datetime.now(UTC).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    watchlists = db.relationship("UserWatchlist", backref="user", lazy=True)
    preferences = db.relationship("UserPreference", backref="user", uselist=False, lazy=True)
    saved_stock_data = db.relationship("SavedStockData", backref="user", lazy=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.password_hash = sha256.hash(password)

    def check_password(self, password):
        return sha256.verify(password, self.password_hash)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Stock(db.Model):
    __tablename__ = "stocks"
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)
    last_updated = db.Column(db.DateTime, onupdate=utcnow)

    watchlists = db.relationship("UserWatchlist", backref="stock", lazy=True)
    saved_data_points = db.relationship("SavedStockData", backref="stock", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "exchange": self.exchange,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    def __repr__(self):
        return f"<Stock {self.symbol}>"


class UserWatchlist(db.Model):
    __tablename__ = "user_watchlist"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey("stocks.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "stock_id", name="uq_user_stock_watchlist"),)

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.stock.symbol,
            "name": self.stock.name,
            "exchange": self.stock.exchange,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }

    def __repr__(self):
        return f"<UserWatchlist user_id={self.user_id} stock_id={self.stock_id}>"


class UserPreference(db.Model):
    __tablename__ = "user_preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    notification_frequency = db.Column(
        db.Enum(*NOTIFICATION_FREQUENCIES, name="notification_frequency_enum"), default="daily"
    )
    notification_type_email = db.Column(db.Boolean, default=True)
    notification_type_inapp = db.Column(db.Boolean, default=True)
    report_fields = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_frequency": self.notification_frequency,
            "notification_type_email": self.notification_type_email,
            "notification_type_inapp": self.notification_type_inapp,
            "report_fields": self.report_fields,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<UserPreference user_id={self.user_id}>"


class SavedStockData(db.Model):
    __tablename__ = "saved_stock_data"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey("stocks.id"), nullable=False)
    data_point_name = db.Column(db.String(255), nullable=False)
    data_value = db.Column(db.Text, nullable=False)
    saved_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stock_id": self.stock_id,
            "stock_symbol": self.stock.symbol if self.stock else None,
            "data_point_name": self.data_point_name,
            "data_value": self.data_value,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }

    def __repr__(self):
        return f"<SavedStockData user_id={self.user_id} stock_id={self.stock_id} name={self.data_point_name}>"
