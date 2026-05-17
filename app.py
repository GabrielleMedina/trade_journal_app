from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///trade.db')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.before_request
def create_tables():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class JournalEntry(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date)
    amount_risked = db.Column(db.Float, default=0)
    pnl = db.Column(db.Float, default=0)
    portfolio_change = db.Column(db.Float, default=0)
    result = db.Column(db.String(20), default="Unknown")
    notes = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<JournalEntry %r>' % self.id

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        form_email = request.form['email'].strip()
        form_username = request.form['username'].strip()
        form_password = request.form['password'].strip()
        
        existing_user = User.query.filter_by(email=form_email).first()
        if existing_user:
            flash("An account with that email already exists.", 'error')
            return redirect(url_for('register'))
        
        if len(form_password) < 8:
            flash("Password must be at least 8 characters.", 'error')
            return redirect(url_for('register'))
        
        has_upper = any(char.isupper() for char in form_password)
        has_lower = any(char.islower() for char in form_password)
        has_digit = any(char.isdigit() for char in form_password)
        has_special = any(not char.isalnum() for char in form_password)

        if not all([has_upper, has_lower, has_digit, has_special]):
            flash('Password must contain uppercase, lowercase, a number, and a special character.', 'error')
            return redirect(url_for('register'))

        new_user = User(
            username=form_username,
            email=form_email
        )
        new_user.set_password(form_password)

        try: 
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully. Please log in.', 'success')
            return redirect(url_for("login"))
        except Exception:
            db.session.rollback()
            flash('Something went wrong creating your account. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False  
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Incorrect email or password. Please try again.', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=remember)
        return redirect(url_for('dashboard'))
    return render_template('login.html')

    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/dashboard")
@login_required
def dashboard():
    date_now = datetime.now()
    weekly_date = date_now - timedelta(days=date_now.weekday())
    monthly_date = (date_now - timedelta(days=30))
    yearly_date = (date_now - timedelta(days=365))

    yearly_entries = JournalEntry.query.filter(
        JournalEntry.date >= yearly_date.date(),
        JournalEntry.user_id == current_user.id
    ).order_by(JournalEntry.date.asc()).all()

    monthly_entries = JournalEntry.query.filter(
        JournalEntry.date >= monthly_date.date(),
        JournalEntry.user_id == current_user.id
    ).order_by(JournalEntry.date.asc()).all()

    weekly_entries = JournalEntry.query.filter(
        JournalEntry.date >= weekly_date.date(),
        JournalEntry.user_id == current_user.id
    ).order_by(JournalEntry.date.asc()).all()

    yearly_pnl = sum([entry.pnl for entry in yearly_entries])
    monthly_pnl = sum([entry.pnl for entry in monthly_entries])
    weekly_pnl = sum([entry.pnl for entry in weekly_entries])

    win_count = 0
    win_rate = 0
    chart_labels = []
    chart_values = []
    running_total = 0
    calendar_events = []

    for entry in monthly_entries:
        chart_labels.append(entry.date.strftime("%Y-%m-%d"))
        running_total += entry.pnl
        chart_values.append(running_total)

        if entry.result == "win":
            event_color = "#22c55e"
        elif entry.result == "loss":
            event_color = "#ef4444"
        else:
            event_color = "#A9A9A9"

        calendar_events.append({
            "start": entry.date.strftime("%Y-%m-%d"),
            "pnl": entry.pnl,
            "portfolio_change": entry.portfolio_change,
            "color": event_color,
        })

    for entry in yearly_entries: 
        if entry.result == 'win': 
            win_count += 1

    if len(yearly_entries) > 0:
        win_rate = round((win_count / len(yearly_entries)) * 100, 2)

    return render_template(
        "dashboard.html", 
        weekly_pnl=weekly_pnl, 
        monthly_pnl=monthly_pnl, 
        yearly_pnl=yearly_pnl, 
        win_rate=win_rate, 
        entries=weekly_entries,
        chart_labels=chart_labels,
        chart_values=chart_values,
        calendar_events=calendar_events
    )


@app.route("/entries")
@login_required
def entries():
    entries = JournalEntry.query.filter(
        JournalEntry.user_id == current_user.id
    ).order_by(JournalEntry.date.desc()).all()
    return render_template("entries.html", entries=entries)

   
@app.route("/new_entry", methods=['POST', 'GET'])
@login_required
def new_entry():
    if request.method == 'POST':
        form_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        form_amount_risked = float(request.form['amount_risked'])
        form_pnl = float(request.form['pnl'])
        form_portfolio_change = float(request.form['portfolio_change'])
        form_result = request.form['result'].strip()
        form_notes = request.form['notes'].strip()
        
        new_entry = JournalEntry(
            user_id=current_user.id,
            date=form_date,
            amount_risked=form_amount_risked,
            pnl=form_pnl,
            portfolio_change=form_portfolio_change,
            result=form_result,
            notes=form_notes
        )
        try: 
            db.session.add(new_entry)
            db.session.commit()
            return redirect(url_for("entries"))
        except Exception:
            db.session.rollback()
            flash('Something went wrong saving your entry. Please try again.', 'error')
            return redirect(url_for('new_entry'))

    return render_template("new_entry.html")


@app.route("/edit_entry/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id):
    entry = db.get_or_404(JournalEntry, entry_id)
    if request.method == 'POST':
        form_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        form_amount_risked = float(request.form['amount_risked'])
        form_pnl = float(request.form['pnl'])
        form_portfolio_change = float(request.form['portfolio_change'])
        form_result = request.form['result'].strip()
        form_notes = request.form['notes'].strip()

        entry.date = form_date
        entry.amount_risked = form_amount_risked
        entry.pnl = form_pnl
        entry.portfolio_change = form_portfolio_change
        entry.result = form_result
        entry.notes = form_notes

        try: 
            db.session.commit()
            return redirect(url_for("entries"))
        except Exception:
            db.session.rollback()
            flash('Something went wrong saving your changes. Please try again.', 'error')
            return redirect(url_for('edit_entry', entry_id=entry_id))

    return render_template("edit_entry.html", entry=entry)


@app.route('/delete_entry/<int:entry_id>', methods=["POST"])
@login_required
def delete_entry(entry_id):
    entry = db.get_or_404(JournalEntry, entry_id)
    try: 
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("entries"))
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting your entry. Please try again.', 'error')
        return redirect(url_for('entries'))