import pytest
from unittest.mock import MagicMock
from flask import Flask, request, session, flash, redirect, url_for
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

@pytest.fixture
def app():
    # Fake render_template to avoid needing template files
    render_template = MagicMock(return_value='')

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user:
                return render_template('home.html', username=user.username)
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            if not username or not password:
                flash('Please enter both username and password.', 'error')
                return render_template('login.html')
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password.', 'error')
                return render_template('login.html')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            if not username or not password or not confirm_password:
                flash('All fields are required.', 'error')
                return render_template('register.html')
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return render_template('register.html')
            if len(password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return render_template('register.html')
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists.', 'error')
                return render_template('register.html')
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class TestLogin:
    def test_login_success(self, app, client):
        """Happy path: valid credentials redirect to home and flash success."""
        with app.app_context():
            user = User(username='testuser',
                        password_hash=generate_password_hash('secret123'))
            db.session.add(user)
            db.session.commit()

        with client:
            resp = client.post('/login', data={
                'username': 'testuser',
                'password': 'secret123'
            })
            assert resp.status_code == 302
            assert resp.location == '/'
            flashes = session['_flashes']
            assert any(msg == 'Login successful!' for cat, msg in flashes)

    def test_login_invalid(self, app, client):
        """Edge case: wrong password flashes error and stays on login page."""
        with app.app_context():
            user = User(username='testuser2',
                        password_hash=generate_password_hash('secret123'))
            db.session.add(user)
            db.session.commit()

        with client:
            resp = client.post('/login', data={
                'username': 'testuser2',
                'password': 'wrongpass'
            })
            assert resp.status_code == 200
            flashes = session['_flashes']
            assert any(msg == 'Invalid username or password.' for cat, msg in flashes)

    def test_login_missing_fields(self, client):
        """Edge case: missing username/password gives error flash."""
        with client:
            resp = client.post('/login', data={})
            assert resp.status_code == 200
            flashes = session['_flashes']
            assert any(msg == 'Please enter both username and password.' for cat, msg in flashes)


class TestRegister:
    def test_register_success(self, client):
        """Happy path: registration creates user, redirects to login."""
        with client:
            resp = client.post('/register', data={
                'username': 'newuser',
                'password': 'sixchar',
                'confirm_password': 'sixchar'
            })
            assert resp.status_code == 302
            assert resp.location == '/login'
            flashes = session['_flashes']
            assert any(msg == 'Registration successful! You can now log in.' for cat, msg in flashes)

            # Verify user was actually created
            user = User.query.filter_by(username='newuser').first()
            assert user is not None

    def test_register_duplicate(self, app, client):
        """Edge case: duplicate username flashes error."""
        with app.app_context():
            user = User(username='existing',
                        password_hash=generate_password_hash('123456'))
            db.session.add(user)
            db.session.commit()

        with client:
            resp = client.post('/register', data={
                'username': 'existing',
                'password': '123456',
                'confirm_password': '123456'
            })
            assert resp.status_code == 200
            flashes = session['_flashes']
            assert any(msg == 'Username already exists.' for cat, msg in flashes)


class TestHome:
    def test_home_unauthenticated(self, client):
        """Edge case: accessing / without login redirects to /login."""
        resp = client.get('/')
        assert resp.status_code == 302
        assert resp.location == '/login'

    def test_logout(self, app, client):
        """Happy path: logout clears session and redirects to login."""
        with app.app_context():
            user = User(username='logoutuser',
                        password_hash=generate_password_hash('123456'))
            db.session.add(user)
            db.session.commit()

        with client:
            # Log in first
            client.post('/login', data={
                'username': 'logoutuser',
                'password': '123456'
            })
            # Then logout
            resp = client.get('/logout')
            assert resp.status_code == 302
            assert resp.location == '/login'
            flashes = session['_flashes']
            assert any(msg == 'You have been logged out.' for cat, msg in flashes)
            # Verify session cleared
            with client.session_transaction() as sess:
                assert 'user_id' not in sess