from datetime import date
from flask import Blueprint, request, jsonify
from sqlalchemy import func, or_
from werkzeug.security import generate_password_hash
from models.models import (db, User, Course, Exam, Rubric, Slot, Booking,
                           Evaluation)
from helpers import (role_required, err, parse_date, parse_time, has_clash,
                     take_seat, free_seat)
import cache

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
admin_only = role_required('admin')

EXAM_STATUSES = ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']


# ---------------- dashboard ----------------

@admin_bp.route('/stats')
@admin_only
def stats():
    data = cache.get('admin:stats')
    if data is None:
        popular = db.session.query(Exam.name, func.count(Booking.id)) \
            .join(Booking, Booking.exam_id == Exam.id) \
            .filter(Booking.status != 'Cancelled') \
            .group_by(Exam.id).order_by(func.count(Booking.id).desc()).limit(5).all()
        workload = db.session.query(User.name, func.count(Slot.id)) \
            .join(Slot, Slot.examiner_id == User.id) \
            .group_by(User.id).order_by(func.count(Slot.id).desc()).limit(5).all()
        data = {
            'courses': Course.query.count(),
            'exams': Exam.query.count(),
            'students': User.query.filter_by(role='student').count(),
            'examiners': User.query.filter_by(role='examiner').count(),
            'bookings': Booking.query.filter(Booking.status == 'Booked').count(),
            'completed': Booking.query.filter(Booking.status == 'Completed').count(),
            'popular_exams': [{'name': n, 'count': c} for n, c in popular],
            'examiner_workload': [{'name': n, 'count': c} for n, c in workload],
        }
        cache.put('admin:stats', data, 60)
    return jsonify(data)


# ---------------- courses ----------------

@admin_bp.route('/courses')
@admin_only
def list_courses():
    return jsonify([c.to_dict() for c in Course.query.order_by(Course.code).all()])


@admin_bp.route('/courses', methods=['POST'])
@admin_only
def add_course():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    name = (data.get('name') or '').strip()
    if not code or not name:
        return err('Course code and name are required')
    if Course.query.filter_by(code=code).first():
        return err('Course code already exists')
    course = Course(code=code, name=name, description=data.get('description'),
                    status=data.get('status', 'Active'))
    db.session.add(course)
    db.session.commit()
    cache.clear('admin:')
    return jsonify(course.to_dict()), 201


@admin_bp.route('/courses/<int:cid>', methods=['PUT'])
@admin_only
def edit_course(cid):
    course = Course.query.get_or_404(cid)
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    name = (data.get('name') or '').strip()
    if not code or not name:
        return err('Course code and name are required')
    other = Course.query.filter(Course.code == code, Course.id != cid).first()
    if other:
        return err('Course code already exists')
    course.code = code
    course.name = name
    course.description = data.get('description')
    course.status = data.get('status', course.status)
    db.session.commit()
    cache.clear('exams:')
    return jsonify(course.to_dict())


@admin_bp.route('/courses/<int:cid>', methods=['DELETE'])
@admin_only
def delete_course(cid):
    course = Course.query.get_or_404(cid)
    if Exam.query.filter_by(course_id=cid).first():
        return err('This course has examinations, remove them first')
    db.session.delete(course)
    db.session.commit()
    cache.clear('admin:')
    return jsonify(message='Course removed')


# ---------------- exams ----------------

def fill_exam(exam, data):
    # copies fields from request to exam, returns an error text if something is wrong
    name = (data.get('name') or '').strip()
    course = Course.query.get(data.get('course_id') or 0)
    if not name:
        return 'Examination name is required'
    if not course:
        return 'Select a valid course'
    try:
        duration = int(data.get('duration'))
        max_marks = int(data.get('max_marks'))
    except (TypeError, ValueError):
        return 'Duration and maximum marks must be numbers'
    if duration <= 0 or max_marks <= 0:
        return 'Duration and maximum marks must be greater than 0'

    ss = parse_date(data.get('slot_create_start'))
    se = parse_date(data.get('slot_create_end'))
    bs = parse_date(data.get('booking_start'))
    be = parse_date(data.get('booking_end'))
    if not (ss and se and bs and be):
        return 'All four timeline dates are required'
    if ss > se:
        return 'Slot creation end date is before the start date'
    if bs > be:
        return 'Booking end date is before the start date'

    exam.name = name
    exam.course_id = course.id
    exam.exam_type = data.get('exam_type', 'Examination')
    exam.duration = duration
    exam.max_marks = max_marks
    exam.slot_create_start, exam.slot_create_end = ss, se
    exam.booking_start, exam.booking_end = bs, be
    exam.instructions = data.get('instructions')
    return None


@admin_bp.route('/exams')
@admin_only
def list_exams():
    return jsonify([e.to_dict() for e in Exam.query.order_by(Exam.id.desc()).all()])


@admin_bp.route('/exams', methods=['POST'])
@admin_only
def add_exam():
    exam = Exam(status='Draft')
    problem = fill_exam(exam, request.get_json() or {})
    if problem:
        return err(problem)
    db.session.add(exam)
    db.session.commit()
    cache.clear('admin:')
    cache.clear('exams:')
    return jsonify(exam.to_dict()), 201


@admin_bp.route('/exams/<int:eid>', methods=['PUT'])
@admin_only
def edit_exam(eid):
    exam = Exam.query.get_or_404(eid)
    problem = fill_exam(exam, request.get_json() or {})
    if problem:
        return err(problem)
    db.session.commit()
    cache.clear('exams:')
    return jsonify(exam.to_dict())


@admin_bp.route('/exams/<int:eid>', methods=['DELETE'])
@admin_only
def delete_exam(eid):
    exam = Exam.query.get_or_404(eid)
    if Booking.query.filter_by(exam_id=eid).first():
        return err('Students have bookings for this examination, it cannot be deleted')
    Slot.query.filter_by(exam_id=eid).delete()
    Rubric.query.filter_by(exam_id=eid).delete()
    exam.examiners = []
    db.session.delete(exam)
    db.session.commit()
    cache.clear('admin:')
    cache.clear('exams:')
    return jsonify(message='Examination deleted')


@admin_bp.route('/exams/<int:eid>/status', methods=['PUT'])
@admin_only
def change_status(eid):
    # this is how admin opens / closes slot creation and student booking
    exam = Exam.query.get_or_404(eid)
    status = (request.get_json() or {}).get('status')
    if status not in EXAM_STATUSES:
        return err('Invalid status')
    if status == 'Slot Creation' and not exam.examiners:
        return err('Assign at least one examiner before opening slot creation')
    if status == 'Booking Open':
        has_slot = Slot.query.filter_by(exam_id=eid, status='Available').first()
        if not has_slot:
            return err('There are no available slots to open booking')
    exam.status = status
    db.session.commit()
    cache.clear('exams:')
    return jsonify(exam.to_dict())


@admin_bp.route('/exams/<int:eid>/examiners', methods=['PUT'])
@admin_only
def assign_examiners(eid):
    exam = Exam.query.get_or_404(eid)
    ids = (request.get_json() or {}).get('examiner_ids', [])
    examiners = User.query.filter(User.id.in_(ids), User.role == 'examiner').all()
    exam.examiners = examiners
    db.session.commit()
    cache.clear('exams:')
    return jsonify(exam.to_dict())


# ---------------- rubrics ----------------

@admin_bp.route('/exams/<int:eid>/rubrics')
@admin_only
def list_rubrics(eid):
    rubrics = Rubric.query.filter_by(exam_id=eid).all()
    return jsonify([r.to_dict() for r in rubrics])


def check_rubric(exam, data, skip_id=None):
    criterion = (data.get('criterion') or '').strip()
    if not criterion:
        return None, 'Criterion name is required'
    try:
        weightage = int(data.get('weightage'))
    except (TypeError, ValueError):
        return None, 'Weightage must be a number'
    if weightage <= 0:
        return None, 'Weightage must be greater than 0'
    others = Rubric.query.filter(Rubric.exam_id == exam.id, Rubric.id != skip_id).all()
    total = sum(r.weightage for r in others)
    if total + weightage > exam.max_marks:
        return None, 'Total weightage cannot be more than maximum marks (%d)' % exam.max_marks
    return (criterion, weightage), None



@admin_bp.route('/exams/<int:eid>/rubrics', methods=['POST'])
@admin_only
def add_rubric(eid):
    exam = Exam.query.get_or_404(eid)
    data = request.get_json() or {}
    values, problem = check_rubric(exam, data)
    if problem:
        return err(problem)
    rubric = Rubric(exam_id=eid, criterion=values[0], weightage=values[1],
                    description=data.get('description'))
    db.session.add(rubric)
    db.session.commit()
    return jsonify(rubric.to_dict()), 201


@admin_bp.route('/rubrics/<int:rid>', methods=['PUT'])
@admin_only
def edit_rubric(rid):
    rubric = Rubric.query.get_or_404(rid)
    exam = Exam.query.get(rubric.exam_id)
    data = request.get_json() or {}
    values, problem = check_rubric(exam, data, skip_id=rid)
    if problem:
        return err(problem)
    rubric.criterion, rubric.weightage = values
    rubric.description = data.get('description')
    db.session.commit()
    return jsonify(rubric.to_dict())


@admin_bp.route('/rubrics/<int:rid>', methods=['DELETE'])
@admin_only
def delete_rubric(rid):
    rubric = Rubric.query.get_or_404(rid)
    db.session.delete(rubric)
    db.session.commit()
    return jsonify(message='Rubric removed')


# ---------------- examiners and students ----------------

@admin_bp.route('/examiners')
@admin_only
def list_examiners():
    users = User.query.filter_by(role='examiner').order_by(User.name).all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/examiners', methods=['POST'])
@admin_only
def add_examiner():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    name = (data.get('name') or '').strip()
    password = data.get('password') or ''
    if not username or not name or '@' not in email:
        return err('Name, username and a valid email are required')
    if len(password) < 6:
        return err('Password must have at least 6 characters')
    if User.query.filter_by(username=username).first():
        return err('Username already taken')
    if User.query.filter_by(email=email).first():
        return err('Email already registered')
    user = User(username=username, email=email, name=name, role='examiner',
                password=generate_password_hash(password),
                phone=data.get('phone'), department=data.get('department'))
    db.session.add(user)
    db.session.commit()
    cache.clear('admin:')
    return jsonify(user.to_dict()), 201


@admin_bp.route('/examiners/<int:uid>', methods=['PUT'])
@admin_only
def edit_examiner(uid):
    user = User.query.filter_by(id=uid, role='examiner').first_or_404()
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    if not name or '@' not in email:
        return err('Name and a valid email are required')
    other = User.query.filter(User.email == email, User.id != uid).first()
    if other:
        return err('Email already used by someone else')
    user.name = name
    user.email = email
    user.phone = data.get('phone')
    user.department = data.get('department')
    user.status = data.get('status', user.status)
    if data.get('password'):
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(user.to_dict())


@admin_bp.route('/students')
@admin_only
def list_students():
    users = User.query.filter_by(role='student').order_by(User.name).all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route('/students/<int:uid>/status', methods=['PUT'])
@admin_only
def student_status(uid):
    user = User.query.filter_by(id=uid, role='student').first_or_404()
    status = (request.get_json() or {}).get('status')
    if status not in ('Active', 'Inactive'):
        return err('Invalid status')
    user.status = status
    db.session.commit()
    return jsonify(user.to_dict())


# ---------------- slots and bookings ----------------

@admin_bp.route('/slots')
@admin_only
def all_slots():
    query = Slot.query
    if request.args.get('exam_id'):
        query = query.filter_by(exam_id=request.args['exam_id'])
    slots = query.order_by(Slot.date, Slot.start_time).all()
    return jsonify([s.to_dict() for s in slots])


@admin_bp.route('/slots/<int:sid>', methods=['PUT'])
@admin_only
def reschedule_slot(sid):
    # change date / time of a slot (exceptional cases)
    slot = Slot.query.get_or_404(sid)
    data = request.get_json() or {}
    day = parse_date(data.get('date'))
    start = parse_time(data.get('start_time'))
    end = parse_time(data.get('end_time'))
    if not (day and start and end):
        return err('Date, start time and end time are required')
    if start >= end:
        return err('End time must be after start time')
    if has_clash(slot.examiner_id, day, start, end, skip_id=slot.id):
        return err('Examiner already has a slot at that time')
    slot.date, slot.start_time, slot.end_time = day, start, end
    db.session.commit()
    return jsonify(slot.to_dict())


@admin_bp.route('/slots/<int:sid>/examiner', methods=['PUT'])
@admin_only
def change_examiner(sid):
    slot = Slot.query.get_or_404(sid)
    new = User.query.filter_by(id=(request.get_json() or {}).get('examiner_id'),
                               role='examiner', status='Active').first()
    if not new:
        return err('Select a valid active examiner')
    if has_clash(new.id, slot.date, slot.start_time, slot.end_time, skip_id=slot.id):
        return err('That examiner already has a slot at this time')
    slot.examiner_id = new.id
    if new not in slot.exam.examiners:
        slot.exam.examiners.append(new)
    db.session.commit()
    return jsonify(slot.to_dict())


@admin_bp.route('/bookings')
@admin_only
def all_bookings():
    # includes cancelled and completed ones, so this is also the history
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return jsonify([b.to_dict() for b in bookings])


@admin_bp.route('/bookings/<int:bid>/reschedule', methods=['PUT'])
@admin_only
def reschedule_booking(bid):
    booking = Booking.query.get_or_404(bid)
    if booking.status != 'Booked':
        return err('Only active bookings can be rescheduled')
    new_slot = Slot.query.get((request.get_json() or {}).get('slot_id') or 0)
    if not new_slot or new_slot.exam_id != booking.exam_id:
        return err('Select a slot of the same examination')
    if new_slot.id == booking.slot_id:
        return err('Student is already in this slot')
    if new_slot.status != 'Available':
        return err('That slot is not available')
    if not take_seat(new_slot):
        return err('That slot is full')
    free_seat(booking.slot)
    booking.slot_id = new_slot.id
    db.session.commit()
    return jsonify(booking.to_dict())


# ---------------- search ----------------

@admin_bp.route('/search')
@admin_only
def search():
    q = (request.args.get('q') or '').strip()
    kind = request.args.get('type', 'students')
    like = '%' + q + '%'

    if kind == 'students' or kind == 'examiners':
        role = 'student' if kind == 'students' else 'examiner'
        rows = User.query.filter(User.role == role, or_(
            User.name.like(like), User.username.like(like), User.email.like(like))).all()
        return jsonify([u.to_dict() for u in rows])

    if kind == 'exams':
        rows = Exam.query.join(Course).filter(or_(
            Exam.name.like(like), Course.name.like(like), Course.code.like(like))).all()
        return jsonify([e.to_dict() for e in rows])

    if kind == 'bookings':
        rows = Booking.query.join(User, Booking.student_id == User.id) \
            .join(Exam, Booking.exam_id == Exam.id) \
            .filter(or_(User.name.like(like), Exam.name.like(like))).all()
        return jsonify([b.to_dict() for b in rows])

    return err('Unknown search type')
