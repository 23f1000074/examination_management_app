from datetime import datetime
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from models.models import db, Slot


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            verify_jwt_in_request()
            if get_jwt().get('role') not in roles:
                return jsonify(message='You are not allowed to do this'), 403
            return fn(*args, **kwargs)
        return inner
    return decorator


def current_user_id():
    return int(get_jwt_identity())


def err(message, code=400):
    return jsonify(message=message), code


def parse_date(text):
    try:
        return datetime.strptime(text, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_time(text):
    try:
        return datetime.strptime(text[:5], '%H:%M').time()
    except (ValueError, TypeError):
        return None


def has_clash(examiner_id, day, start, end, skip_id=None):
    # true if the examiner already has a slot overlapping this time
    slots = Slot.query.filter(Slot.examiner_id == examiner_id, Slot.date == day,
                              Slot.status != 'Cancelled').all()
    for s in slots:
        if s.id == skip_id:
            continue
        if start < s.end_time and s.start_time < end:
            return True
    return False


def take_seat(slot):
    # single UPDATE with a condition so two students cannot take the last seat
    done = Slot.query.filter(Slot.id == slot.id, Slot.available_seats > 0).update(
        {'available_seats': Slot.available_seats - 1})
    if done == 0:
        return False
    db.session.refresh(slot)
    if slot.available_seats == 0:
        slot.status = 'Full'
    return True


def free_seat(slot):
    if slot.available_seats < slot.capacity:
        slot.available_seats += 1
    if slot.status == 'Full':
        slot.status = 'Available'
