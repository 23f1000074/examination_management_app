import os
import csv
import json
import smtplib
import urllib.request
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from celery import Celery
from celery.schedules import crontab

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, 'exports')
REPORT_DIR = os.path.join(BASE_DIR, 'reports')

REDIS_URL = os.environ.get('CELERY_BROKER', 'redis://127.0.0.1:6379/0')
celery = Celery('emp', broker=REDIS_URL, backend=REDIS_URL)
celery.conf.timezone = 'Asia/Kolkata'

# beat schedule: reminder every morning 8am, report on 1st of every month
celery.conf.beat_schedule = {
    'daily-reminder': {
        'task': 'tasks.daily_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'monthly-report': {
        'task': 'tasks.monthly_report',
        'schedule': crontab(day_of_month=1, hour=7, minute=0),
    },
}

_app = None


def get_app():
    # import here to avoid circular import (app -> routes -> tasks)
    global _app
    if _app is None:
        from app import create_app
        _app = create_app()
    return _app


def send_chat(text):
    # Google Chat webhook, if no url is set the message is only printed
    url = os.environ.get('CHAT_WEBHOOK_URL')
    if not url:
        print('[CHAT]', text)
        return
    body = json.dumps({'text': text}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print('Chat webhook failed:', e)


@celery.task(name='tasks.daily_reminders')
def daily_reminders():
    from models.models import Booking
    app = get_app()
    with app.app_context():
        last_day = date.today() + timedelta(days=1)
        bookings = Booking.query.filter(Booking.status == 'Booked').all()
        count = 0
        for b in bookings:
            if not (date.today() <= b.slot.date <= last_day):
                continue
            text = ('Reminder for %s\nExamination: %s\nDate and time: %s %s-%s\n'
                    'Examiner: %s\nInstructions: %s') % (
                b.student.name, b.exam.name, b.slot.date,
                b.slot.start_time.strftime('%H:%M'), b.slot.end_time.strftime('%H:%M'),
                b.slot.examiner.name, b.exam.instructions or 'Carry your ID card')
            send_chat(text)
            count += 1
    return count


def build_report(year, month):
    from models.models import Slot, Booking, Evaluation, User
    first = date(year, month, 1)
    nxt = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

    slots = Slot.query.filter(Slot.date >= first, Slot.date < nxt).all()
    exams_conducted = len(set(s.exam_id for s in slots))
    month_bookings = [b for b in Booking.query.all() if first <= b.slot.date < nxt]
    completed = [b for b in month_bookings if b.status == 'Completed']
    pending = [b for b in month_bookings if b.status == 'Booked']
    evaluated = [b for b in month_bookings if b.evaluation]

    counts = {}
    for b in evaluated:
        name = b.slot.examiner.name
        counts[name] = counts.get(name, 0) + 1
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

    html = '<h2>Examination report - %s</h2><ul>' % first.strftime('%B %Y')
    html += '<li>Examinations conducted: %d</li>' % exams_conducted
    html += '<li>Students evaluated: %d</li>' % len(evaluated)
    html += '<li>Completed bookings: %d</li>' % len(completed)
    html += '<li>Pending evaluations: %d</li></ul>' % len(pending)
    html += '<h3>Most active examiners</h3><ol>'
    for name, c in top:
        html += '<li>%s (%d evaluations)</li>' % (name, c)
    html += '</ol>'
    return html


@celery.task(name='tasks.monthly_report')
def monthly_report():
    from models.models import User
    app = get_app()
    with app.app_context():
        # report is for the previous month
        last_month_day = date.today().replace(day=1) - timedelta(days=1)
        html = build_report(last_month_day.year, last_month_day.month)
        admin = User.query.filter_by(role='admin').first()

        host = os.environ.get('SMTP_HOST')
        if not host:
            os.makedirs(REPORT_DIR, exist_ok=True)
            path = os.path.join(REPORT_DIR, 'report_%d_%02d.html' % (last_month_day.year, last_month_day.month))
            with open(path, 'w') as f:
                f.write(html)
            print('SMTP not set, report saved to', path)
            return path

        msg = MIMEText(html, 'html')
        msg['Subject'] = 'Monthly examination report'
        msg['From'] = os.environ.get('MAIL_FROM', 'emp@localhost')
        msg['To'] = admin.email
        with smtplib.SMTP(host, int(os.environ.get('SMTP_PORT', 587))) as server:
            server.starttls()
            server.login(os.environ.get('SMTP_USER', ''), os.environ.get('SMTP_PASS', ''))
            server.send_message(msg)
        return 'sent'


@celery.task(name='tasks.export_history')
def export_history(student_id):
    from models.models import User, Booking
    app = get_app()
    with app.app_context():
        student = User.query.get(student_id)
        bookings = Booking.query.filter_by(student_id=student_id).order_by(Booking.id).all()

        os.makedirs(EXPORT_DIR, exist_ok=True)
        filename = 'history_%d_%s.csv' % (student_id, datetime.now().strftime('%Y%m%d%H%M%S'))
        with open(os.path.join(EXPORT_DIR, filename), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['Examination Name', 'Course', 'Examination Date', 'Examiner',
                        'Marks Obtained', 'Booking Status'])
            for b in bookings:
                marks = b.evaluation.marks if b.evaluation else ''
                w.writerow([b.exam.name, b.exam.course.name, b.slot.date,
                            b.slot.examiner.name, marks, b.status])

        send_chat('Hi %s, your examination history export (%s) is ready. '
                  'Download it from your dashboard.' % (student.name, filename))
    return filename
