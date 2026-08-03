from datetime import date, datetime

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from trekking_app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    approval_status = db.Column(db.String(20), nullable=False, default="approved")
    is_account_active = db.Column(db.Boolean, nullable=False, default=True)
    is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    assigned_treks = db.relationship(
        "Trek",
        back_populates="assigned_staff",
        foreign_keys="Trek.assigned_staff_id",
        lazy="selectin",
    )
    bookings = db.relationship("Booking", back_populates="user", lazy="selectin")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff_member(self):
        return self.role == "staff"

    @property
    def is_trekker(self):
        return self.role == "user"

    @property
    def is_approved(self):
        if self.is_staff_member:
            return self.approval_status == "approved"
        return True

    @property
    def is_pending_approval(self):
        return self.is_staff_member and self.approval_status == "pending"

    @property
    def is_rejected(self):
        return self.is_staff_member and self.approval_status == "rejected"

    @property
    def can_access_system(self):
        return self.is_account_active and not self.is_blacklisted and self.is_approved

    @property
    def role_label(self):
        labels = {
            "admin": "Admin",
            "staff": "Trek Staff",
            "user": "Trekker",
        }
        return labels.get(self.role, "User")

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="closed")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    assigned_staff = db.relationship(
        "User",
        back_populates="assigned_treks",
        foreign_keys=[assigned_staff_id],
        lazy="joined",
    )
    bookings = db.relationship("Booking", back_populates="trek", lazy="selectin")

    @property
    def active_booking_count(self):
        return sum(1 for booking in self.bookings if booking.status == "booked")

    @property
    def available_slots(self):
        return max(self.total_slots - self.active_booking_count, 0)

    def __repr__(self):
        return f"<Trek {self.id} {self.name}>"


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("user_id", "trek_id", name="uq_booking_user_trek"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), nullable=False, default="booked")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("User", back_populates="bookings", lazy="joined")
    trek = db.relationship("Trek", back_populates="bookings", lazy="joined")

    def __repr__(self):
        return f"<Booking {self.id} user={self.user_id} trek={self.trek_id}>"
