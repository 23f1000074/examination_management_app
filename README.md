# Examination Management Portal (EMP) - V2

Flask (API) + Vue 3 + Bootstrap + SQLite + Redis + Celery.

## Setup

Needs Python 3.10+, Node 18+ and a Redis server running on localhost:6379.

### Backend
```
cd backend
pip install -r requirements.txt
python app.py
```
The database (`emp.db`) and the admin user are created automatically on first run.

Admin login: `admin` / `admin123`  (change with env vars ADMIN_USERNAME, ADMIN_PASSWORD)

### Celery (separate terminals, inside `backend`)
```
celery -A tasks.celery worker --loglevel=info -P solo
celery -A tasks.celery beat --loglevel=info
```
(`-P solo` is needed on Windows.)

### Frontend
```
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Optional settings (environment variables)
- `CHAT_WEBHOOK_URL` - Google Chat webhook for reminders / export alerts (if not set, messages are printed in the celery console)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_FROM` - for the monthly report email (if not set, the report is saved in `backend/reports`)

## Typical flow to demo
1. Admin: add course -> add examiner -> create examination -> add rubric -> assign examiner
2. Admin: set status to "Slot Creation"
3. Examiner: create slots
4. Admin: set status to "Booking Open"
5. Student: register, book a slot
6. Examiner: open slot students, evaluate with rubric
7. Student: see result and export history CSV
