from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from trekking_app.services.auth_service import get_dashboard_endpoint

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for(get_dashboard_endpoint(current_user)))
    return render_template("main/home.html")
