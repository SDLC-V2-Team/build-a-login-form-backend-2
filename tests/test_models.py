import os
import sys
import pytest

# Ensure the project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, User
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def app():
    """Create a fresh Flask app with an in‑memory SQLite database."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_create_user_happy_path(app):
    """A valid user can be created and retrieved with correct fields."""
    with app.app_context():
        user = User(username='testuser', password_hash='hashed_secret')
        db.session.add(user)
        db.session.commit()

        retrieved = User.query.filter_by(username='testuser').first()
        assert retrieved is not None
        assert retrieved.username == 'testuser'
        assert retrieved.password_hash == 'hashed_secret'
        assert 'testuser' in repr(retrieved)


def test_unique_username(app):
    """Creating a second user with the same username raises IntegrityError."""
    with app.app_context():
        user1 = User(username='duplicate', password_hash='pw1')
        db.session.add(user1)
        db.session.commit()

        user2 = User(username='duplicate', password_hash='pw2')
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        # Rollback so the session can be used again
        db.session.rollback()


def test_create_user_with_max_username_length(app):
    """Username of exactly 80 characters is stored correctly."""
    with app.app_context():
        username = 'a' * 80
        user = User(username=username, password_hash='pw')
        db.session.add(user)
        db.session.commit()

        retrieved = User.query.filter_by(username=username).first()
        assert retrieved is not None
        assert len(retrieved.username) == 80


def test_create_user_with_exceeding_username_length(app):
    """Username of 81 characters does not raise an error (SQLite leniency)."""
    with app.app_context():
        username = 'a' * 81
        user = User(username=username, password_hash='pw')
        db.session.add(user)
        # Should not raise; commit succeeds because SQLite does not enforce length
        db.session.commit()

        retrieved = User.query.filter_by(username=username).first()
        assert retrieved is not None
        assert len(retrieved.username) == 81


def test_user_missing_username(app):
    """Omitting the username (None) raises IntegrityError on commit."""
    with app.app_context():
        user = User(password_hash='pw')  # username is None by default
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


def test_user_missing_password_hash(app):
    """Omitting the password_hash (None) raises IntegrityError on commit."""
    with app.app_context():
        user = User(username='user')  # password_hash is None by default
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()



def test_repr(app):
    """The __repr__ method returns the expected string."""
    with app.app_context():
        user = User(username='repruser', password_hash='pw')
        db.session.add(user)
        db.session.commit()

        assert repr(user) == '<User repruser>'


def test_dotenv_import():
    """python-dotenv must be importable (production dependency)."""
    import dotenv
    assert hasattr(dotenv, 'load_dotenv'), "dotenv.load_dotenv not found"
