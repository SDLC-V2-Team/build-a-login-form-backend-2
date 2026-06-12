import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
