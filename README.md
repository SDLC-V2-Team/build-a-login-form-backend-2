# Login Form App

A simple Flask web application with user registration and login, using SQLite for persistent storage.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser at `http://localhost:5000`.

## Configuration

- `SECRET_KEY`: Set via environment variable or defaults to `dev-secret-key-change-in-production`.
- `PORT`: Server port (default 5000).
- The SQLite database `users.db` is created automatically in the instance folder.

## Routes

- `/` - home page (requires login)
- `/login` - login form
- `/register` - registration form
- `/logout` - logs out the user

## Design Decisions

- Passwords are hashed using Werkzeug's `generate_password_hash` (PBKDF2).
- Sessions are managed with Flask's built-in signed cookies using `SECRET_KEY`.
- Database uses SQLite via Flask-SQLAlchemy.
