from sqlalchemy import String, cast, or_
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from trekking_app.admin.forms import TrekForm
from trekking_app.decorators import role_required
from trekking_app.extensions import db
from trekking_app.models import Booking, Trek, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@role_required("admin")
def dashboard():
    total_treks = Trek.query.filter_by(is_archived=False).count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role="staff", approval_status="pending").count()
    blacklisted_accounts = User.query.filter_by(is_blacklisted=True).count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    recent_treks = (
        Trek.query.filter_by(is_archived=False)
        .order_by(Trek.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        current_section="dashboard",
        user=current_user,
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        pending_staff=pending_staff,
        blacklisted_accounts=blacklisted_accounts,
        recent_bookings=recent_bookings,
        recent_treks=recent_treks,
    )


@admin_bp.route("/treks")
@role_required("admin")
def treks():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    difficulty_filter = request.args.get("difficulty", "all")

    query = Trek.query

    if status_filter == "archived":
        query = query.filter(Trek.is_archived.is_(True))
    else:
        query = query.filter(Trek.is_archived.is_(False))
        if status_filter != "all":
            query = query.filter(Trek.status == status_filter)

    if difficulty_filter != "all":
        query = query.filter(Trek.difficulty == difficulty_filter)

    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                cast(Trek.id, String).ilike(pattern),
                Trek.name.ilike(pattern),
                Trek.location.ilike(pattern),
            )
        )

    treks = query.order_by(Trek.start_date.asc(), Trek.id.desc()).all()

    return render_template(
        "admin/treks.html",
        current_section="treks",
        treks=treks,
        search_term=search_term,
        status_filter=status_filter,
        difficulty_filter=difficulty_filter,
    )


@admin_bp.route("/treks/create", methods=["GET", "POST"])
@role_required("admin")
def create_trek():
    form = TrekForm()
    form.assigned_staff_id.choices = build_staff_choices()

    if form.validate_on_submit():
        if form.status.data != "closed" and form.assigned_staff_id.data == 0:
            flash("Assign an approved staff member before setting a trek as active.", "warning")
        else:
            trek = Trek()
            populate_trek_from_form(trek, form)
            db.session.add(trek)
            db.session.commit()
            flash("Trek created successfully.", "success")
            return redirect(url_for("admin.treks"))

    return render_template(
        "admin/trek_form.html",
        current_section="treks",
        form=form,
        page_title="Add New Trek",
        submit_label="Create Trek",
    )


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_trek(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    form = TrekForm(obj=trek)
    form.assigned_staff_id.choices = build_staff_choices(trek.assigned_staff_id)

    if request.method == "GET":
        form.assigned_staff_id.data = trek.assigned_staff_id or 0

    if form.validate_on_submit():
        if form.total_slots.data < trek.active_booking_count:
            flash(
                f"Total slots cannot be lower than the current active bookings ({trek.active_booking_count}).",
                "danger",
            )
        elif form.status.data != "closed" and form.assigned_staff_id.data == 0:
            flash("Assign an approved staff member before setting a trek as active.", "warning")
        else:
            populate_trek_from_form(trek, form)
            db.session.commit()
            flash("Trek updated successfully.", "success")
            return redirect(url_for("admin.treks"))

    return render_template(
        "admin/trek_form.html",
        current_section="treks",
        form=form,
        trek=trek,
        page_title="Edit Trek",
        submit_label="Save Changes",
    )


@admin_bp.route("/treks/<int:trek_id>/archive", methods=["POST"])
@role_required("admin")
def archive_trek(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    trek.is_archived = True
    trek.status = "archived"
    db.session.commit()
    flash("Trek archived successfully. Historical data remains preserved.", "info")
    return redirect(url_for("admin.treks"))


@admin_bp.route("/treks/<int:trek_id>/restore", methods=["POST"])
@role_required("admin")
def restore_trek(trek_id):
    trek = db.get_or_404(Trek, trek_id)
    trek.is_archived = False
    if trek.status == "archived":
        trek.status = "closed"
    db.session.commit()
    flash("Trek restored successfully.", "success")
    return redirect(url_for("admin.treks", status="archived"))


@admin_bp.route("/staff")
@role_required("admin")
def staff_list():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")

    query = User.query.filter_by(role="staff")

    if status_filter == "blacklisted":
        query = query.filter(User.is_blacklisted.is_(True))
    elif status_filter in {"pending", "approved", "rejected"}:
        query = query.filter(User.approval_status == status_filter)

    if search_term:
        query = apply_user_search(query, search_term)

    staff_members = query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin/staff.html",
        current_section="staff",
        staff_members=staff_members,
        search_term=search_term,
        status_filter=status_filter,
    )


@admin_bp.route("/staff/<int:user_id>/approve", methods=["POST"])
@role_required("admin")
def approve_staff(user_id):
    staff_member = get_role_user_or_404(user_id, "staff")
    staff_member.approval_status = "approved"
    staff_member.is_account_active = True
    db.session.commit()
    flash(f"{staff_member.full_name} has been approved as trek staff.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:user_id>/reject", methods=["POST"])
@role_required("admin")
def reject_staff(user_id):
    staff_member = get_role_user_or_404(user_id, "staff")
    staff_member.approval_status = "rejected"
    db.session.commit()
    flash(f"{staff_member.full_name} has been marked as not approved.", "warning")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:user_id>/toggle-blacklist", methods=["POST"])
@role_required("admin")
def toggle_staff_blacklist(user_id):
    staff_member = get_role_user_or_404(user_id, "staff")
    set_blacklist_state(staff_member, should_blacklist=not staff_member.is_blacklisted)

    if staff_member.is_blacklisted:
        flash(f"{staff_member.full_name} has been blacklisted.", "danger")
    else:
        flash(f"{staff_member.full_name} has been removed from the blacklist.", "success")

    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/users")
@role_required("admin")
def users_list():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")

    query = User.query.filter_by(role="user")

    if status_filter == "blacklisted":
        query = query.filter(User.is_blacklisted.is_(True))
    elif status_filter == "active":
        query = query.filter(User.is_blacklisted.is_(False), User.is_account_active.is_(True))

    if search_term:
        query = apply_user_search(query, search_term)

    trekkers = query.order_by(User.created_at.desc()).all()

    return render_template(
        "admin/users.html",
        current_section="users",
        trekkers=trekkers,
        search_term=search_term,
        status_filter=status_filter,
    )


@admin_bp.route("/users/<int:user_id>/toggle-blacklist", methods=["POST"])
@role_required("admin")
def toggle_user_blacklist(user_id):
    trekker = get_role_user_or_404(user_id, "user")
    set_blacklist_state(trekker, should_blacklist=not trekker.is_blacklisted)

    if trekker.is_blacklisted:
        flash(f"{trekker.full_name} has been blacklisted.", "danger")
    else:
        flash(f"{trekker.full_name} has been removed from the blacklist.", "success")

    return redirect(url_for("admin.users_list"))


@admin_bp.route("/bookings")
@role_required("admin")
def bookings_list():
    search_term = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")

    query = Booking.query.join(User, Booking.user_id == User.id).join(Trek, Booking.trek_id == Trek.id)

    if status_filter != "all":
        query = query.filter(Booking.status == status_filter)

    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                cast(Booking.id, String).ilike(pattern),
                User.full_name.ilike(pattern),
                Trek.name.ilike(pattern),
            )
        )

    bookings = query.order_by(Booking.created_at.desc()).all()

    return render_template(
        "admin/bookings.html",
        current_section="bookings",
        bookings=bookings,
        search_term=search_term,
        status_filter=status_filter,
    )


@admin_bp.route("/search")
@role_required("admin")
def search():
    search_term = request.args.get("q", "").strip()
    staff_results = []
    user_results = []
    trek_results = []

    if search_term:
        staff_results = (
            apply_user_search(User.query.filter_by(role="staff"), search_term)
            .order_by(User.full_name.asc())
            .limit(10)
            .all()
        )
        user_results = (
            apply_user_search(User.query.filter_by(role="user"), search_term)
            .order_by(User.full_name.asc())
            .limit(10)
            .all()
        )
        pattern = f"%{search_term}%"
        trek_results = (
            Trek.query.filter(
                or_(
                    cast(Trek.id, String).ilike(pattern),
                    Trek.name.ilike(pattern),
                    Trek.location.ilike(pattern),
                )
            )
            .order_by(Trek.start_date.asc())
            .limit(10)
            .all()
        )

    return render_template(
        "admin/search.html",
        current_section="search",
        search_term=search_term,
        staff_results=staff_results,
        user_results=user_results,
        trek_results=trek_results,
    )


def build_staff_choices(selected_staff_id=None):
    approved_staff = (
        User.query.filter_by(role="staff", approval_status="approved", is_blacklisted=False, is_account_active=True)
        .order_by(User.full_name.asc())
        .all()
    )
    choices = [(0, "Unassigned")]
    included_ids = {0}

    for staff_member in approved_staff:
        choices.append((staff_member.id, f"{staff_member.full_name} (#{staff_member.id})"))
        included_ids.add(staff_member.id)

    if selected_staff_id and selected_staff_id not in included_ids:
        staff_member = db.session.get(User, selected_staff_id)
        if staff_member:
            choices.append((staff_member.id, f"{staff_member.full_name} (#{staff_member.id})"))

    return choices


def populate_trek_from_form(trek, form):
    trek.name = form.name.data.strip()
    trek.location = form.location.data.strip()
    trek.difficulty = form.difficulty.data
    trek.duration_days = form.duration_days.data
    trek.total_slots = form.total_slots.data
    trek.start_date = form.start_date.data
    trek.end_date = form.end_date.data
    trek.assigned_staff_id = form.assigned_staff_id.data or None
    trek.status = form.status.data
    trek.description = (form.description.data or "").strip() or None


def apply_user_search(query, search_term):
    pattern = f"%{search_term}%"
    return query.filter(
        or_(
            cast(User.id, String).ilike(pattern),
            User.full_name.ilike(pattern),
            User.email.ilike(pattern),
        )
    )


def get_role_user_or_404(user_id, role):
    user = db.get_or_404(User, user_id)
    if user.role != role:
        abort(404)
    return user


def set_blacklist_state(user, should_blacklist):
    user.is_blacklisted = should_blacklist
    user.is_account_active = not should_blacklist
    db.session.commit()
