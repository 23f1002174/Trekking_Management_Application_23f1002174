from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from trekking_app.auth.forms import LoginForm, RegistrationForm
from trekking_app.extensions import db
from trekking_app.models import User
from trekking_app.services.auth_service import (
    get_dashboard_endpoint,
    is_safe_redirect_url,
    normalize_email,
    normalize_phone,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(get_dashboard_endpoint(current_user)))

    form = LoginForm()

    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
        elif user.is_blacklisted or not user.is_account_active:
            flash(
                "Your account is inactive or blacklisted. Please contact the administrator.",
                "danger",
            )
        else:
            login_user(user, remember=form.remember_me.data)

            if user.is_staff_member and not user.is_approved:
                if user.is_rejected:
                    flash(
                        "Your staff account has not been approved. Please contact the administrator.",
                        "warning",
                    )
                else:
                    flash(
                        "Registration successful. Your staff account is pending admin approval.",
                        "warning",
                    )
                return redirect(url_for("auth.account_status"))

            next_page = request.args.get("next")
            flash("Login successful.", "success")

            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)

            return redirect(url_for(get_dashboard_endpoint(user)))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(get_dashboard_endpoint(current_user)))

    form = RegistrationForm()

    if form.validate_on_submit():
        role = form.role.data
        new_user = User(
            full_name=form.full_name.data.strip(),
            email=normalize_email(form.email.data),
            phone=normalize_phone(form.phone.data),
            role=role,
            approval_status="pending" if role == "staff" else "approved",
            is_account_active=True,
            is_blacklisted=False,
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        if role == "staff":
            flash(
                "Staff registration submitted successfully. Please wait for admin approval before accessing the staff dashboard.",
                "success",
            )
        else:
            flash("Account created successfully. You can now log in.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/account-status")
@login_required
def account_status():
    if current_user.is_blacklisted or not current_user.is_account_active:
        logout_user()
        flash(
            "Your account is inactive or blacklisted. Please contact the administrator.",
            "danger",
        )
        return redirect(url_for("auth.login"))

    if not current_user.is_staff_member:
        return redirect(url_for(get_dashboard_endpoint(current_user)))

    if current_user.is_approved:
        return redirect(url_for("staff.dashboard"))

    return render_template("auth/account_status.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
