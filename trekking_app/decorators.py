from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required, logout_user

from trekking_app.services.auth_service import get_dashboard_endpoint


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.is_blacklisted or not current_user.is_account_active:
                logout_user()
                flash(
                    "Your account is inactive or blacklisted. Please contact the administrator.",
                    "danger",
                )
                return redirect(url_for("auth.login"))

            if current_user.is_staff_member and not current_user.is_approved:
                if current_user.is_rejected:
                    flash(
                        "Your staff account was not approved. Please contact the administrator.",
                        "warning",
                    )
                else:
                    flash(
                        "Your staff account is awaiting admin approval.",
                        "warning",
                    )
                return redirect(url_for("auth.account_status"))

            if current_user.role not in roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for(get_dashboard_endpoint(current_user)))

            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator
