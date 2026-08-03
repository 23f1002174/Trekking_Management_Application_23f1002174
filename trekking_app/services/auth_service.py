from urllib.parse import urljoin, urlparse

from flask import request


def get_dashboard_endpoint(user):
    if not user or not getattr(user, "is_authenticated", False):
        return "main.home"

    if user.is_admin:
        return "admin.dashboard"

    if user.is_staff_member:
        if user.is_approved:
            return "staff.dashboard"
        return "auth.account_status"

    if user.is_trekker:
        return "trekker.dashboard"

    return "main.home"


def is_safe_redirect_url(target):
    if not target:
        return False

    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc


def normalize_email(email):
    return email.strip().lower()


def normalize_phone(phone):
    return "".join(character for character in phone if character.isdigit())
