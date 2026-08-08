from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from trekking_app.decorators import role_required
from trekking_app.extensions import db
from trekking_app.models import Booking, Trek
from trekking_app.staff.forms import SlotsUpdateForm, StaffProfileForm, TrekStatusForm

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")

VALID_TRANSITIONS = {
    "open": ["open", "closed", "started"],
    "closed": ["closed", "open"],
    "started": ["started", "completed"],
    "completed": ["completed"],
}


def get_staff_trek_or_404(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    if trek.assigned_staff_id != current_user.id:
        abort(403)
    return trek


def get_allowed_statuses(current_status):
    return VALID_TRANSITIONS.get(current_status, [current_status])


@staff_bp.route("/")
@role_required("staff")
def dashboard():
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=current_user.id,
        is_archived=False,
    ).all()

    total_assigned = len(assigned_treks)
    open_treks = sum(1 for t in assigned_treks if t.status == "open")
    started_treks = sum(1 for t in assigned_treks if t.status == "started")
    completed_treks = sum(1 for t in assigned_treks if t.status == "completed")
    total_participants = sum(t.active_booking_count for t in assigned_treks)

    recent_treks = (
        Trek.query.filter_by(assigned_staff_id=current_user.id, is_archived=False)
        .order_by(Trek.start_date.asc())
        .limit(5)
        .all()
    )

    return render_template(
        "staff/dashboard.html",
        current_section="dashboard",
        user=current_user,
        total_assigned=total_assigned,
        open_treks=open_treks,
        started_treks=started_treks,
        completed_treks=completed_treks,
        total_participants=total_participants,
        recent_treks=recent_treks,
    )


@staff_bp.route("/treks")
@role_required("staff")
def my_treks():
    status_filter = request.args.get("status", "all")

    query = Trek.query.filter_by(
        assigned_staff_id=current_user.id,
        is_archived=False,
    )

    if status_filter != "all":
        query = query.filter(Trek.status == status_filter)

    treks = query.order_by(Trek.start_date.asc()).all()

    return render_template(
        "staff/treks.html",
        current_section="treks",
        treks=treks,
        status_filter=status_filter,
    )


@staff_bp.route("/treks/<int:trek_id>")
@role_required("staff")
def trek_detail(trek_id):
    trek = get_staff_trek_or_404(trek_id)

    participants = (
        Booking.query.filter_by(trek_id=trek.id, status="booked")
        .order_by(Booking.booking_date.asc())
        .all()
    )
    all_bookings = (
        Booking.query.filter_by(trek_id=trek.id)
        .order_by(Booking.booking_date.asc())
        .all()
    )

    status_form = TrekStatusForm()
    allowed_statuses = get_allowed_statuses(trek.status)
    status_form.status.choices = [
        (s, s.capitalize()) for s in allowed_statuses
    ]
    status_form.status.data = trek.status

    slots_form = SlotsUpdateForm()
    slots_form.available_slots.data = trek.available_slots

    return render_template(
        "staff/trek_detail.html",
        current_section="treks",
        trek=trek,
        participants=participants,
        all_bookings=all_bookings,
        status_form=status_form,
        slots_form=slots_form,
    )


@staff_bp.route("/treks/<int:trek_id>/status", methods=["POST"])
@role_required("staff")
def update_trek_status(trek_id):
    trek = get_staff_trek_or_404(trek_id)

    allowed = get_allowed_statuses(trek.status)
    allowed_statuses = [s for s in allowed]

    status_form = TrekStatusForm()
    status_form.status.choices = [(s, s.capitalize()) for s in allowed_statuses]

    if status_form.validate_on_submit():
        new_status = status_form.status.data
        if new_status not in allowed_statuses:
            flash("Invalid status transition.", "danger")
            return redirect(url_for("staff.trek_detail", trek_id=trek.id))

        old_status = trek.status
        trek.status = new_status

        if new_status == "completed" and old_status != "completed":
            for booking in trek.bookings:
                if booking.status == "booked":
                    booking.status = "completed"

        db.session.commit()
        flash(f"Trek status updated to '{new_status.capitalize()}'.", "success")
    else:
        flash("Invalid form submission.", "danger")

    return redirect(url_for("staff.trek_detail", trek_id=trek.id))


@staff_bp.route("/treks/<int:trek_id>/slots", methods=["POST"])
@role_required("staff")
def update_trek_slots(trek_id):
    trek = get_staff_trek_or_404(trek_id)

    slots_form = SlotsUpdateForm()
    if slots_form.validate_on_submit():
        new_slots = slots_form.available_slots.data
        active_bookings = trek.active_booking_count

        if new_slots < active_bookings:
            flash(
                f"Available slots cannot be set below current active bookings ({active_bookings}).",
                "danger",
            )
        else:
            trek.total_slots = trek.total_slots - trek.available_slots + new_slots
            db.session.commit()
            flash(f"Available slots updated to {new_slots}.", "success")
    else:
        flash("Invalid value. Please enter a non-negative whole number.", "danger")

    return redirect(url_for("staff.trek_detail", trek_id=trek.id))


@staff_bp.route("/profile", methods=["GET", "POST"])
@role_required("staff")
def profile():
    form = StaffProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip()
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("staff.profile"))

    return render_template(
        "staff/profile.html",
        current_section="profile",
        form=form,
        user=current_user,
    )
