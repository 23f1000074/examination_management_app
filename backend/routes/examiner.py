from datetime import date
from flask import Blueprint, request, jsonify
from models.models import (db, User, Exam, Rubric, Slot, Booking, Evaluation,
                           EvaluationScore)
from helpers import (role_required, err, current_user_id, parse_date,
                     parse_time, has_clash)
import cache

examiner_bp = Blueprint('examiner', __name__, url_prefix='/api/examiner')
examiner_only = role_required('examiner')


def my_exams(uid):
    me = User.query.get(uid)
    return Exam.query.filter(Exam.examiners.contains(me)).all()


@examiner_bp.route('/dashboard')
@examiner_only
def dashboard():
    uid = current_user_id()
    slots = Slot.query.filter_by(examiner_id=uid).all()
    slot_ids = [s.id for s in slots]
    booked = Booking.query.filter(Booking.slot_id.in_(slot_ids), Booking.status != 'Cancelled').count() if slot_ids else 0
    pending = Booking.query.filter(Booking.slot_id.in_(slot_ids), Booking.status == 'Booked').count() if slot_ids else 0
    return jsonify({
        'exams': [e.to_dict() for e in my_exams(uid)],
        'slot_count': len(slots),
        'booked_students': booked,
        'pending_evaluations': pending,
    })


@examiner_bp.route('/slots')
@examiner_only
def my_slots():
    slots = Slot.query.filter_by(examiner_id=current_user_id()) \
        .order_by(Slot.date, Slot.start_time).all()
    return jsonify([s.to_dict() for s in slots])


def read_slot(data, exam):
    day = parse_date(data.get('date'))
    start = parse_time(data.get('start_time'))
    end = parse_time(data.get('end_time'))
    try:
        capacity = int(data.get('capacity'))
    except (TypeError, ValueError):
        return None, 'Capacity must be a number'
    if not (day and start and end):
        return None, 'Date, start time and end time are required'
    if start >= end:
        return None, 'End time must be after start time'
    if capacity < 1:
        return None, 'Capacity must be at least 1'
    if day < date.today():
        return None, 'Slot date cannot be in the past'
    return (day, start, end, capacity), None


@examiner_bp.route('/slots', methods=['POST'])
@examiner_only
def create_slot():
    uid = current_user_id()
    data = request.get_json() or {}
    exam = Exam.query.get(data.get('exam_id') or 0)
    me = User.query.get(uid)
    if not exam or me not in exam.examiners:
        return err('This examination is not assigned to you', 403)

    # slots can be created only in the slot creation period
    today = date.today()
    if exam.status != 'Slot Creation':
        return err('Slot creation is not open for this examination')
    if not (exam.slot_create_start <= today <= exam.slot_create_end):
        return err('Today is outside the slot creation dates')

    values, problem = read_slot(data, exam)
    if problem:
        return err(problem)
    day, start, end, capacity = values
    if has_clash(uid, day, start, end):
        return err('You already have a slot at this time')

    slot = Slot(exam_id=exam.id, examiner_id=uid, date=day, start_time=start,
                end_time=end, capacity=capacity, available_seats=capacity)
    db.session.add(slot)
    db.session.commit()
    return jsonify(slot.to_dict()), 201


@examiner_bp.route('/slots/<int:sid>', methods=['PUT'])
@examiner_only
def update_slot(sid):
    slot = Slot.query.filter_by(id=sid, examiner_id=current_user_id()).first_or_404()
    # only before student booking starts
    if slot.exam.status != 'Slot Creation':
        return err('Slots can be changed only before booking starts')
    values, problem = read_slot(request.get_json() or {}, slot.exam)
    if problem:
        return err(problem)
    day, start, end, capacity = values
    if has_clash(slot.examiner_id, day, start, end, skip_id=slot.id):
        return err('You already have a slot at this time')
    slot.date, slot.start_time, slot.end_time = day, start, end
    slot.capacity = capacity
    slot.available_seats = capacity
    db.session.commit()
    return jsonify(slot.to_dict())


@examiner_bp.route('/slots/<int:sid>', methods=['DELETE'])
@examiner_only
def delete_slot(sid):
    slot = Slot.query.filter_by(id=sid, examiner_id=current_user_id()).first_or_404()
    if slot.exam.status != 'Slot Creation':
        return err('Slots can be removed only before booking starts')
    db.session.delete(slot)
    db.session.commit()
    return jsonify(message='Slot removed')


@examiner_bp.route('/slots/<int:sid>/students')
@examiner_only
def slot_students(sid):
    slot = Slot.query.filter_by(id=sid, examiner_id=current_user_id()).first_or_404()
    bookings = Booking.query.filter(Booking.slot_id == slot.id,
                                    Booking.status != 'Cancelled').all()
    return jsonify([b.to_dict() for b in bookings])


@examiner_bp.route('/bookings/<int:bid>/evaluation')
@examiner_only
def get_evaluation(bid):
    booking = Booking.query.get_or_404(bid)
    if booking.slot.examiner_id != current_user_id():
        return err('This student is not booked in your slot', 403)
    rubrics = Rubric.query.filter_by(exam_id=booking.exam_id).all()
    given = {}
    remarks = ''
    if booking.evaluation:
        remarks = booking.evaluation.remarks
        for s in booking.evaluation.scores:
            given[s.rubric_id] = s.marks
    return jsonify({
        'booking': booking.to_dict(),
        'max_marks': booking.exam.max_marks,
        'remarks': remarks,
        'rubrics': [dict(r.to_dict(), marks=given.get(r.id, 0)) for r in rubrics],
    })


@examiner_bp.route('/bookings/<int:bid>/evaluate', methods=['POST'])
@examiner_only
def evaluate(bid):
    booking = Booking.query.get_or_404(bid)
    if booking.slot.examiner_id != current_user_id():
        return err('You can evaluate only students booked in your slots', 403)
    if booking.status == 'Cancelled':
        return err('This booking was cancelled')

    data = request.get_json() or {}
    rubrics = {r.id: r for r in Rubric.query.filter_by(exam_id=booking.exam_id).all()}
    if not rubrics:
        return err('Admin has not created a rubric for this examination yet')

    scores = {}
    for item in data.get('scores', []):
        rid = item.get('rubric_id')
        try:
            marks = int(item.get('marks'))
        except (TypeError, ValueError):
            return err('Marks must be numbers')
        if rid not in rubrics:
            return err('Unknown rubric')
        if marks < 0 or marks > rubrics[rid].weightage:
            return err('Marks for "%s" must be between 0 and %d' % (rubrics[rid].criterion, rubrics[rid].weightage))
        scores[rid] = marks
    if len(scores) != len(rubrics):
        return err('Give marks for every rubric criterion')

    ev = booking.evaluation
    if ev is None:
        ev = Evaluation(booking_id=booking.id, student_id=booking.student_id)
        db.session.add(ev)
    ev.scores = [EvaluationScore(rubric_id=rid, marks=m) for rid, m in scores.items()]
    ev.marks = sum(scores.values())
    ev.remarks = (data.get('remarks') or '').strip()
    ev.status = 'Published'
    booking.status = 'Completed'
    db.session.commit()
    cache.clear('admin:')
    return jsonify(message='Marks submitted', marks=ev.marks)


@examiner_bp.route('/exams/<int:eid>/status', methods=['PUT'])
@examiner_only
def exam_status(eid):
    exam = Exam.query.get_or_404(eid)
    me = User.query.get(current_user_id())
    if me not in exam.examiners:
        return err('This examination is not assigned to you', 403)
    status = (request.get_json() or {}).get('status')
    # examiner can only close the booking or mark the exam as completed
    if status not in ('Closed', 'Completed'):
        return err('You can only set Closed or Completed')
    if status == 'Completed' and exam.status not in ('Booking Open', 'Closed'):
        return err('Examination must be in booking/closed stage first')
    exam.status = status
    if status == 'Completed':
        Slot.query.filter(Slot.exam_id == eid, Slot.status != 'Cancelled').update({'status': 'Completed'})
    db.session.commit()
    cache.clear('exams:')
    return jsonify(exam.to_dict())
