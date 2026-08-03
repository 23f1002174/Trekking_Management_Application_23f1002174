from datetime import date

from sqlalchemy import or_

from trekking_app.models import Booking, Trek


def apply_trek_filters(query, search_term="", difficulty_filter="all", location_filter=""):
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Trek.name.ilike(pattern),
                Trek.location.ilike(pattern),
            )
        )

    if difficulty_filter != "all":
        query = query.filter(Trek.difficulty == difficulty_filter)

    if location_filter:
        query = query.filter(Trek.location.ilike(location_filter))

    return query


def get_location_options():
    return [
        location
        for location, in Trek.query.with_entities(Trek.location)
        .filter(Trek.is_archived.is_(False))
        .distinct()
        .order_by(Trek.location.asc())
        .all()
    ]


def get_bookable_trek_query():
    return Trek.query.filter(
        Trek.is_archived.is_(False),
        Trek.status == "open",
        Trek.start_date >= date.today(),
    )


def get_existing_booking(user_id, trek_id):
    return Booking.query.filter_by(user_id=user_id, trek_id=trek_id).first()


def validate_booking_request(user, trek):
    if trek.is_archived:
        return "This trek is archived and cannot be booked."

    if trek.status != "open":
        return "This trek is not open for booking."

    if trek.start_date < date.today():
        return "This trek has already started or is no longer available for booking."

    if trek.available_slots <= 0:
        return "No slots are available for this trek."

    existing_booking = get_existing_booking(user.id, trek.id)
    if existing_booking:
        if existing_booking.status == "booked":
            return "You have already booked this trek."
        return "A booking record already exists for this trek."

    return None


def can_cancel_booking(booking):
    if booking.status != "booked":
        return False

    if booking.trek.status in {"started", "completed", "archived"}:
        return False

    return booking.trek.start_date > date.today()
