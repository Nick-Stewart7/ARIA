# Flask Task Manager

A comprehensive web application built with Flask that provides task management functionality with user authentication, REST API, and a responsive web interface.

## Features

- User Authentication with Sessions
- REST API with CRUD Operations
- Database Integration with SQLAlchemy (3 related tables)
- Input Validation and Error Handling
- Security Measures (CSRF protection, password hashing)
- HTML Interface with Forms
- Unit Tests

## Quick Start

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open browser to http://localhost:5000

5. Login with default admin account:
   - Username: admin
   - Password: admin123

## Project Structure

- app.py - Flask application factory
- models.py - Database models (User, Role, Task)
- forms.py - WTForms form definitions
- tests.py - Unit tests
- routes/ - Route blueprints for auth, tasks, and API
- templates/ - Jinja2 templates

## API Endpoints

- GET /api/tasks - Get all tasks
- POST /api/tasks - Create new task
- GET /api/tasks/<id> - Get specific task
- PUT /api/tasks/<id> - Update task
- DELETE /api/tasks/<id> - Delete task
- PATCH /api/tasks/<id>/toggle - Toggle completion

## Testing

Run all tests:
```bash
python tests.py
```

## Production Deployment

With Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()
```

## Security Features

- Bcrypt password hashing
- CSRF protection on all forms
- Session management with Flask-Login
- Input validation and sanitization
- User data isolation

## Database Schema

Three related tables:
1. Users - User accounts and authentication
2. Roles - User permission roles
3. Tasks - Task management with user relationships

All tables include proper foreign key relationships and indexes for performance.