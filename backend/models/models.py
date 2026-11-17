from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# which examiners are assigned to which exam
exam_examiners = db.Table(
    'exam_examiners',
    db.Column('exam_id', db.Integer, db.ForeignKey('exam.id'), primary_key=True),
    db.Column('examiner_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)


class User(db.Model):
    # one table for admin, examiner and student (role column tells which)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin / examiner / student
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Active')  # Active / Inactive
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id, 'username': self.username, 'email': self.email,
            'role': self.role, 'name': self.name, 'phone': self.phone,
            'department': self.department, 'status': self.status,
        }


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    status = db.Column(db.String(20), default='Active')

    def to_dict(self):
        return {'id': self.id, 'code': self.code, 'name': self.name,
                'description': self.description, 'status': self.status}


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    exam_type = db.Column(db.String(30), default='Examination')  # Examination / Assessment
    duration = db.Column(db.Integer, nullable=False)  # minutes
    max_marks = db.Column(db.Integer, nullable=False)
    slot_create_start = db.Column(db.Date)
    slot_create_end = db.Column(db.Date)
    booking_start = db.Column(db.Date)
    booking_end = db.Column(db.Date)
    status = db.Column(db.String(20), default='Draft')  # Draft / Slot Creation / Booking Open / Closed / Completed
    instructions = db.Column(db.String(500))

    course = db.relationship('Course')
    examiners = db.relationship('User', secondary=exam_examiners)

    def to_dict(self):
        return {
            'id': self.id, 'course_id': self.course_id,
            'course_code': self.course.code, 'course_name': self.course.name,
            'name': self.name, 'exam_type': self.exam_type,
            'duration': self.duration, 'max_marks': self.max_marks,
            'slot_create_start': str(self.slot_create_start or ''),
            'slot_create_end': str(self.slot_create_end or ''),
            'booking_start': str(self.booking_start or ''),
            'booking_end': str(self.booking_end or ''),
            'status': self.status, 'instructions': self.instructions,
            'examiners': [{'id': e.id, 'name': e.name} for e in self.examiners],
        }


class Rubric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    criterion = db.Column(db.String(100), nullable=False)
    weightage = db.Column(db.Integer, nullable=False)  # max marks for this criterion
    description = db.Column(db.String(300))

    def to_dict(self):
        return {'id': self.id, 'exam_id': self.exam_id, 'criterion': self.criterion,
                'weightage': self.weightage, 'description': self.description}


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available / Full / Cancelled / Completed

    exam = db.relationship('Exam')
    examiner = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id, 'exam_id': self.exam_id, 'exam_name': self.exam.name,
            'examiner_id': self.examiner_id, 'examiner_name': self.examiner.name,
            'date': str(self.date), 'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'capacity': self.capacity, 'available_seats': self.available_seats,
            'status': self.status,
        }


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slot.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Booked')  # Booked / Cancelled / Completed

    student = db.relationship('User')
    slot = db.relationship('Slot')
    exam = db.relationship('Exam')
    evaluation = db.relationship('Evaluation', uselist=False, backref='booking')

    def to_dict(self):
        ev = self.evaluation
        return {
            'id': self.id, 'student_id': self.student_id,
            'student_name': self.student.name, 'exam_id': self.exam_id,
            'exam_name': self.exam.name, 'course': self.exam.course.name,
            'slot_id': self.slot_id, 'date': str(self.slot.date),
            'start_time': self.slot.start_time.strftime('%H:%M'),
            'end_time': self.slot.end_time.strftime('%H:%M'),
            'examiner_name': self.slot.examiner.name,
            'booking_date': self.booking_date.strftime('%Y-%m-%d %H:%M'),
            'status': self.status,
            'evaluated': ev is not None,
        }


class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    marks = db.Column(db.Integer, default=0)
    remarks = db.Column(db.String(500))
    evaluation_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Published')

    scores = db.relationship('EvaluationScore', backref='evaluation', cascade='all, delete-orphan')


class EvaluationScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubric.id'), nullable=False)
    marks = db.Column(db.Integer, nullable=False)

    rubric = db.relationship('Rubric')
