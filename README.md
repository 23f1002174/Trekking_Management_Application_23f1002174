# Trekking Management Application

A role-based web application for managing trekking operations — admins manage treks and users, staff handle assigned treks, and trekkers browse and book adventures.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | SQLAlchemy + SQLite |
| Authentication | Flask-Login |
| Forms & CSRF | Flask-WTF |
| Frontend | Bootstrap 5, Bootstrap Icons |

---

## Project Structure

```
trekking_app/
├── admin/          # Admin blueprint (trek CRUD, user management)
├── auth/           # Auth blueprint (login, register, logout)
├── main/           # Main blueprint (home page)
├── staff/          # Staff blueprint (trek lifecycle, participants)
├── trekker/        # Trekker blueprint (browse, book, history)
├── services/       # Shared business logic (booking, auth helpers)
├── templates/      # Jinja2 HTML templates
├── static/css/     # app.css (design system)
├── models.py       # SQLAlchemy models (User, Trek, Booking)
├── decorators.py   # Role-based access control decorator
├── extensions.py   # Flask extensions (db, login_manager, csrf)
└── __init__.py     # App factory with blueprints and CLI commands
```

---

## How to Run

### 1. Clone or download the project

```bash
cd Trekking_Management_Application_23f1002174
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialise the database

This creates the database tables and seeds the default admin account:

```bash
python -m flask --app app init-db
```

### 5. Run the application

```bash
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

---

## Default Admin Credentials

| Field | Value |
|---|---|
| Email | `admin@trek.local` |
| Password | `Admin@123` |

---

## User Roles

| Role | How to get access |
|---|---|
| **Admin** | Seeded automatically via `init-db` |
| **Trek Staff** | Register with role "Trek Staff" — requires admin approval |
| **Trekker** | Register with role "Trekker" — immediate access |

---

## Key Features

- Admin: create/edit/archive treks, approve or reject staff, manage users and bookings, global search
- Staff: view assigned treks, update status (Open → Started → Completed), manage available slots, view participant lists
- Trekker: browse open treks, book with real-time slot tracking, cancel bookings before trek starts, view full history

---

## Notes

- The database file is stored at `instance/trekking.db`
- Run `init-db` again only if you want to reset the database (it will not overwrite an existing admin)
- All forms are CSRF-protected via Flask-WTF
