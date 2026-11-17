# Adds sample data for testing / demo. Run once:  python seed.py
from datetime import date, time, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from models.models import (db, User, Course, Exam, Rubric, Slot, Booking,
                           Evaluation, EvaluationScore)

app = create_app()
today = date.today()


def add_user(username, name, role, dept, password):
    user = User(username=username, name=name, role=role, department=dept,
                email=username + '@example.com', phone='9876543210',
                password=generate_password_hash(password))
    db.session.add(user)
    return user


def add_slot(exam, examiner, days, start_hour, capacity):
    slot = Slot(exam=exam, examiner=examiner, date=today + timedelta(days=days),
                start_time=time(start_hour, 0), end_time=time(start_hour + 1, 0),
                capacity=capacity, available_seats=capacity)
    db.session.add(slot)
    return slot


def book(student, slot, status='Booked'):
    booking = Booking(student=student, slot=slot, exam=slot.exam, status=status)
    slot.available_seats -= 1
    if slot.available_seats == 0:
        slot.status = 'Full'
    db.session.add(booking)
    return booking


def evaluate(booking, marks_list, remarks):
    ev = Evaluation(booking=booking, student_id=booking.student_id,
                    marks=sum(marks_list), remarks=remarks)
    rubrics = Rubric.query.filter_by(exam_id=booking.exam_id).all()
    ev.scores = [EvaluationScore(rubric_id=r.id, marks=m) for r, m in zip(rubrics, marks_list)]
    db.session.add(ev)
    booking.status = 'Completed'


with app.app_context():
    if Course.query.first():
        print('Sample data already exists, nothing to do.')
        raise SystemExit

    # courses
    cs = Course(code='CS101', name='Introduction to Programming', description='Python basics and problem solving')
    ma = Course(code='MA201', name='Linear Algebra', description='Vectors, matrices and transformations')
    ph = Course(code='PH101', name='Physics Lab', description='Experiments and viva')
    st = Course(code='ST301', name='Statistics', description='Probability and inference')
    db.session.add_all([cs, ma, ph, st])

    # people
    ex1 = add_user('rohan', 'Dr. Rohan Mehta', 'examiner', 'Computer Science', 'examiner123')
    ex2 = add_user('anita', 'Prof. Anita Desai', 'examiner', 'Mathematics', 'examiner123')
    ex3 = add_user('suresh', 'Dr. Suresh Nair', 'examiner', 'Physics', 'examiner123')
    names = [('aarav', 'Aarav Sharma'), ('diya', 'Diya Patel'), ('kabir', 'Kabir Singh'),
             ('meera', 'Meera Iyer'), ('nikhil', 'Nikhil Rao'), ('sara', 'Sara Khan')]
    students = [add_user(u, n, 'student', 'Data Science', 'student123') for u, n in names]
    db.session.flush()

    # exam 1: finished, with results
    e1 = Exam(course=cs, name='Python Viva', exam_type='Examination', duration=20, max_marks=50,
              slot_create_start=today - timedelta(days=30), slot_create_end=today - timedelta(days=20),
              booking_start=today - timedelta(days=19), booking_end=today - timedelta(days=10),
              status='Completed', instructions='Carry your ID card and laptop.', examiners=[ex1])
    # exam 2: students can book right now
    e2 = Exam(course=ma, name='Linear Algebra Mid Viva', exam_type='Examination', duration=30, max_marks=40,
              slot_create_start=today - timedelta(days=5), slot_create_end=today + timedelta(days=2),
              booking_start=today - timedelta(days=1), booking_end=today + timedelta(days=6),
              status='Booking Open', instructions='Bring a pen and ID card.', examiners=[ex2])
    # exam 3: examiners can create slots right now
    e3 = Exam(course=ph, name='Physics Lab Assessment', exam_type='Assessment', duration=25, max_marks=30,
              slot_create_start=today - timedelta(days=1), slot_create_end=today + timedelta(days=7),
              booking_start=today + timedelta(days=8), booking_end=today + timedelta(days=14),
              status='Slot Creation', instructions='Lab coat is compulsory.', examiners=[ex3])
    # exam 4: only draft
    e4 = Exam(course=st, name='Statistics Project Viva', exam_type='Examination', duration=15, max_marks=25,
              slot_create_start=today + timedelta(days=10), slot_create_end=today + timedelta(days=15),
              booking_start=today + timedelta(days=16), booking_end=today + timedelta(days=22),
              status='Draft', instructions='Submit the project report before the viva.')
    db.session.add_all([e1, e2, e3, e4])
    db.session.flush()

    # rubrics (weightage adds up to max marks)
    for exam, items in [
        (e1, [('Logic', 20), ('Code quality', 15), ('Viva answers', 15)]),
        (e2, [('Concepts', 20), ('Problem solving', 20)]),
        (e3, [('Procedure', 10), ('Observation', 10), ('Result', 10)]),
    ]:
        for criterion, weight in items:
            db.session.add(Rubric(exam_id=exam.id, criterion=criterion, weightage=weight))
    db.session.flush()

    # past slots with completed evaluations
    s1 = add_slot(e1, ex1, -12, 10, 3)
    s2 = add_slot(e1, ex1, -11, 14, 3)
    s1.status = s2.status = 'Completed'
    db.session.flush()
    b1 = book(students[0], s1, 'Completed')
    b2 = book(students[1], s1, 'Completed')
    b3 = book(students[2], s2, 'Completed')
    db.session.flush()
    evaluate(b1, [18, 13, 12], 'Good understanding of loops and functions.')
    evaluate(b2, [15, 12, 10], 'Fine, but improve code readability.')
    evaluate(b3, [19, 14, 14], 'Excellent viva, very clear answers.')

    # open booking slots
    s3 = add_slot(e2, ex2, 3, 10, 2)
    s4 = add_slot(e2, ex2, 3, 12, 2)
    s5 = add_slot(e2, ex2, 4, 10, 3)
    db.session.flush()
    book(students[3], s3)
    book(students[4], s3)   # this slot is now full
    book(students[0], s4)

    db.session.commit()
    print('Sample data added.')
    print('Examiners: rohan / anita / suresh  (password: examiner123)')
    print('Students : aarav, diya, kabir, meera, nikhil, sara  (password: student123)')
