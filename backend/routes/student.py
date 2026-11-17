import os
from datetime import date
from flask import Blueprint, request, jsonify, send_from_directory
from sqlalchemy import or_
from models.models import db, Course, Exam, Slot, Booking, Evaluation
from helpers import role_required, err, current_user_id, take_seat, free_seat
import cache
from tasks import export_history, celery, EXPORT_DIR

student_bp = Blueprint('student', __name__, url_prefix='/api/student')
student_only = role_required('student')


def result_dict(b):
    ev = b.evaluation
    return {
        'booking_id': b.id, 'exam_name': b.exam.name, 'course': b.exam.course.name,
        'date': str(b.slot.date), 'examiner_name': b.slot.examiner.name,
        'max_marks': b.exam.max_marks, 'marks': ev.marks, 'remarks': ev.remarks,
        'scores': [{'criterion': s.rubric.criterion, 'max': s.rubric.weightage,
                    'marks': s.marks} for s in ev.scores],
    }


@student_bp.route('/dashboard')
@student_only
def dashboard():
    uid = current_user_id()
    my_bookings = Booking.query.filter_by(student_id=uid).all()
    booked_exam_ids = [b.exam_id for b in my_bookings if b.status != 'Cancelled']

    open_exams = Exam.query.filter(Exam.status == 'Booking Open').all()
    available = [e for e in open_exams if e.id not in booked_exam_ids]
    slot_count = Slot.query.filter(Slot.exam_id.in_([e.id for e in available]),
                                   Slot.status == 'Available').count() if available else 0
    upcoming = Exam.query.filter(Exam.status == 'Slot Creation').all()

    booked = [b.to_dict() for b in my_bookings if b.status == 'Booked']
    results = [result_dict(b) for b in my_bookings
               if b.evaluation and b.evaluation.status == 'Published']
    return jsonify({
        'available_exams': [e.to_dict() for e in available],
        'available_slots': slot_count,
        'upcoming_exams': [e.to_dict() for e in upcoming],
        'booked_slots': booked,
        'results': results,
    })


@student_bp.route('/exams')
@student_only
def search_exams():
    q = (request.args.get('q') or '').strip()
    course_id = request.args.get('course_id', '')
    status = request.args.get('status', '')

    # the list is the same for every student, so it can be cached
    key = 'exams:%s|%s|%s' % (q, course_id, status)
    exams = cache.get(key)
    if exams is None:
        query = Exam.query.join(Course).filter(Exam.status != 'Draft')
        if q:
            like = '%' + q + '%'
            query = query.filter(or_(Exam.name.like(like), Course.name.like(like),
                                     Course.code.like(like)))
        if course_id:
            query = query.filter(Exam.course_id == course_id)
        if status:
            query = query.filter(Exam.status == status)
        exams = [e.to_dict() for e in query.order_by(Exam.id.desc()).all()]
        cache.put(key, exams, 60)

    # booking info is different for each student so it is added after the cache
    mine = {b.exam_id: b.id for b in Booking.query.filter(
        Booking.student_id == current_user_id(), Booking.status != 'Cancelled')}
    for e in exams:
        e['my_booking_id'] = mine.get(e['id'])
    return jsonify(exams)


@student_bp.route('/courses')
@student_only
def course_list():
    return jsonify([c.to_dict() for c in Course.query.order_by(Course.name).all()])


@student_bp.route('/exams/<int:eid>/slots')
@student_only
def exam_slots(eid):
    slots = Slot.query.filter(Slot.exam_id == eid, Slot.status == 'Available') \
        .order_by(Slot.date, Slot.start_time).all()
    return jsonify([s.to_dict() for s in slots])


@student_bp.route('/bookings')
@student_only
def my_bookings():
    bookings = Booking.query.filter_by(student_id=current_user_id()) \
        .order_by(Booking.id.desc()).all()
    return jsonify([b.to_dict() for b in bookings])


@student_bp.route('/bookings', methods=['POST'])
@student_only
def book_slot():
    uid = current_user_id()
    slot = Slot.query.get((request.get_json() or {}).get('slot_id') or 0)
    if not slot:
        return err('Slot not found', 404)
    exam = slot.exam

    today = date.today()
    if exam.status != 'Booking Open':
        return err('Booking is not open for this examination')
    if not (exam.booking_start <= today <= exam.booking_end):
        return err('Today is outside the booking dates')
    if slot.status != 'Available':
        return err('This slot is not available')

    already = Booking.query.filter(Booking.student_id == uid, Booking.exam_id == exam.id,
                                   Booking.status != 'Cancelled').first()
    if already:
        return err('You have already booked a slot for this examination')

    if not take_seat(slot):
        return err('Sorry, the slot just got full')
    booking = Booking(student_id=uid, slot_id=slot.id, exam_id=exam.id)
    db.session.add(booking)
    db.session.commit()
    cache.clear('admin:')
    return jsonify(message='Slot booked', booking=booking.to_dict()), 201


@student_bp.route('/bookings/<int:bid>', methods=['DELETE'])
@student_only
def cancel_booking(bid):
    booking = Booking.query.filter_by(id=bid, student_id=current_user_id()).first_or_404()
    exam = booking.exam
    if booking.status != 'Booked':
        return err('Only active bookings can be cancelled')
    if exam.status != 'Booking Open' or date.today() > exam.booking_end:
        return err('Booking deadline is over, you cannot cancel now')
    booking.status = 'Cancelled'
    free_seat(booking.slot)
    db.session.commit()
    cache.clear('admin:')
    return jsonify(message='Booking cancelled')


@student_bp.route('/results')
@student_only
def results():
    bookings = Booking.query.filter_by(student_id=current_user_id()).all()
    return jsonify([result_dict(b) for b in bookings
                    if b.evaluation and b.evaluation.status == 'Published'])


# ---- csv export (runs as a celery job) ----

@student_bp.route('/export', methods=['POST'])
@student_only
def start_export():
    job = export_history.delay(current_user_id())
    return jsonify(task_id=job.id, message='Export started, you will be alerted when it is ready'), 202


@student_bp.route('/export/<task_id>')
@student_only
def export_status(task_id):
    job = celery.AsyncResult(task_id)
    if job.successful():
        return jsonify(state='done', file=job.result)
    if job.failed():
        return jsonify(state='failed')
    return jsonify(state='running')


@student_bp.route('/export/file/<filename>')
@student_only
def export_download(filename):
    filename = os.path.basename(filename)
    # a student may only download his own file
    if not filename.startswith('history_%d_' % current_user_id()):
        return err('Not allowed', 403)
    return send_from_directory(EXPORT_DIR, filename, as_attachment=True)
