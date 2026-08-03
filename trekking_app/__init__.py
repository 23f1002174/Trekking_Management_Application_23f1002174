from datetime import datetime
from pathlib import Path

import click
from flask import Flask

from config import Config
from trekking_app.admin import admin_bp
from trekking_app.auth import auth_bp
from trekking_app.extensions import csrf, db, login_manager
from trekking_app.main import main_bp
from trekking_app.models import User
from trekking_app.services.auth_service import get_dashboard_endpoint
from trekking_app.staff import staff_bp
from trekking_app.trekker import trekker_bp


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    register_extensions(app)
    register_blueprints(app)
    register_context_processors(app)
    register_error_handlers(app)
    register_cli_commands(app)

    return app


def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "warning"


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(trekker_bp)


def register_context_processors(app):
    @app.context_processor
    def inject_layout_helpers():
        from trekking_app.auth.forms import LogoutForm

        def trek_status_badge(status):
            mapping = {
                "open": "text-bg-success",
                "started": "text-bg-warning",
                "completed": "text-bg-secondary",
                "closed": "text-bg-light border",
                "archived": "text-bg-danger",
            }
            return mapping.get(status, "text-bg-light border")

        return {
            "logout_form": LogoutForm(),
            "get_dashboard_endpoint": get_dashboard_endpoint,
            "current_year": datetime.utcnow().year,
            "trek_status_badge": trek_status_badge,
        }


def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        from flask import flash, redirect, url_for
        flash("You do not have permission to access that resource.", "danger")
        return redirect(url_for("main.home")), 303


def register_cli_commands(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Create the database tables and seed the admin account."""
        db.create_all()
        created_admin = seed_admin(app)

        click.echo("Database initialized successfully.")
        if created_admin:
            click.echo(f"Seeded admin email: {app.config['ADMIN_EMAIL']}")
            click.echo(f"Seeded admin password: {app.config['ADMIN_PASSWORD']}")
        else:
            click.echo("Admin account already exists, so no new admin was created.")


def seed_admin(app):
    admin = User.query.filter_by(email=app.config["ADMIN_EMAIL"]).first()
    if admin:
        return False

    admin = User(
        full_name=app.config["ADMIN_NAME"],
        email=app.config["ADMIN_EMAIL"],
        phone=app.config["ADMIN_PHONE"],
        role="admin",
        approval_status="approved",
        is_account_active=True,
        is_blacklisted=False,
    )
    admin.set_password(app.config["ADMIN_PASSWORD"])

    db.session.add(admin)
    db.session.commit()
    return True


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
