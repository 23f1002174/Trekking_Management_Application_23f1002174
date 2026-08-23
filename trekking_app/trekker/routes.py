from sqlalchemy.orm import selectinload
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from trekking_app.decorators import role_required
from trekking_app.extensions import db
from trekking_app.models import Booking, Trek
from trekking_app.services.auth_service import normalize_email, normalize_phone
from trekking_app.services.booking_service import (
    apply_trek_filters,
    can_cancel_booking,
    get_bookable_trek_query,
    get_existing_booking,
    get_location_options,
    validate_booking_request,
)
from trekking_app.trekker.forms import ProfileForm

trekker_bp = Blueprint("trekker", __name__, url_prefix="/trekker")


@trekker_bp.route("/")
@role_required("user")
def dashboard():
    search_term = request.args.get("q", "").strip()
    difficulty_filter = request.args.get("difficulty", "all")
    location_filter = request.args.get("location", "")

    available_treks_query = apply_trek_filters(
        get_bookable_trek_query(),
        search_term=search_term,
        difficulty_filter=difficulty_filter,
        location_filter=location_filter,
    )
    available_treks = available_treks_query.order_by(Trek.start_date.asc()).limit(6).all()

    active_bookings = (
        Booking.query.filter_by(user_id=current_user.id, status="booked")
        .options(selectinload(Booking.trek))
        .order_by(Booking.booking_date.desc())
        .all()
    )
    history_count = (
        Booking.query.filter(
            Booking.user_id == current_user.id,
            Booking.status.in_(("completed", "cancelled")),
        )
        .count()
    )

    return render_template(
        "trekker/dashboard.html",
        current_section="dashboard",
        user=current_user,
        available_treks=available_treks,
        active_bookings=active_bookings,
        history_count=history_count,
        search_term=search_term,
        difficulty_filter=difficulty_filter,
        location_filter=location_filter,
        location_options=get_location_options(),
    )


@trekker_bp.route("/treks")
@role_required("user")
def browse_treks():
    search_term = request.args.get("q", "").strip()
    difficulty_filter = request.args.get("difficulty", "all")
    location_filter = request.args.get("location", "")

    treks = (
        apply_trek_filters(
            get_bookable_trek_query(),
            search_term=search_term,
            difficulty_filter=difficulty_filter,
            location_filter=location_filter,
        )
        .order_by(Trek.start_date.asc())
        .all()
    )

    booked_trek_ids = {
        booking.trek_id
        for booking in Booking.query.filter_by(
            user_id=current_user.id, status="booked"
        ).all()
    }

    return render_template(
        "trekker/browse.html",
        current_section="browse",
        treks=treks,
        booked_trek_ids=booked_trek_ids,
        search_term=search_term,
        difficulty_filter=difficulty_filter,
        location_filter=location_filter,
        location_options=get_location_options(),
    )


@trekker_bp.route("/treks/<int:trek_id>")
@role_required("user")
def trek_detail(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    existing_booking = get_existing_booking(current_user.id, trek.id)
    active_booking = existing_booking if existing_booking and existing_booking.status == "booked" else None

    return render_template(
        "trekker/trek_detail.html",
        current_section="browse",
        trek=trek,
        existing_booking=active_booking,
    )


@trekker_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@role_required("user")
def book_trek(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    validation_message = validate_booking_request(current_user, trek)

    if validation_message:
        flash(validation_message, "warning")
        return redirect(url_for("trekker.trek_detail", trek_id=trek.id))

    existing = get_existing_booking(current_user.id, trek.id)
    if existing:
        existing.status = "booked"
    else:
        booking = Booking(user_id=current_user.id, trek_id=trek.id, status="booked")
        db.session.add(booking)
    db.session.commit()

    flash("Trek booked successfully.", "success")
    return redirect(url_for("trekker.my_bookings"))


@trekker_bp.route("/bookings")
@role_required("user")
def my_bookings():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .options(selectinload(Booking.trek))
        .filter(Booking.status == "booked")
        .order_by(Booking.booking_date.desc())
        .all()
    )
    return render_template(
        "trekker/bookings.html",
        current_section="bookings",
        bookings=bookings,
        can_cancel_booking=can_cancel_booking,
    )


@trekker_bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@role_required("user")
def cancel_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)

    if booking.user_id != current_user.id:
        flash("You do not have permission to modify this booking.", "danger")
        return redirect(url_for("trekker.my_bookings"))

    if not can_cancel_booking(booking):
        flash("This booking can no longer be cancelled.", "warning")
        return redirect(url_for("trekker.my_bookings"))

    booking.status = "cancelled"
    db.session.commit()
    flash("Booking cancelled successfully.", "info")
    return redirect(url_for("trekker.my_bookings"))


@trekker_bp.route("/history")
@role_required("user")
def history():
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .options(selectinload(Booking.trek))
        .filter(Booking.status.in_(("completed", "cancelled")))
        .order_by(Booking.updated_at.desc())
        .all()
    )
    return render_template(
        "trekker/history.html",
        current_section="history",
        bookings=bookings,
    )


@trekker_bp.route("/profile", methods=["GET", "POST"])
@role_required("user")
def profile():
    form = ProfileForm(original_user_id=current_user.id, obj=current_user)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = normalize_email(form.email.data)
        current_user.phone = normalize_phone(form.phone.data)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("trekker.profile"))

    return render_template(
        "trekker/profile.html",
        current_section="profile",
        form=form,
    )
