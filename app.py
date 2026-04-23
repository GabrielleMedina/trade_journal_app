from flask import Flask, render_template, url_for, request, redirect
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trade.db'
db = SQLAlchemy(app)

class JournalEntry(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    amount_risked =  db.Column(db.Float, default = 0)
    pnl = db.Column(db.Float, default = 0)
    portfolio_change = db.Column(db.Float, default = 0)
    result = db.Column(db.String(20), default="Unknown")
    notes = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<JournalEntry %r>' % self.id
    

@app.route("/")
def index():
    return render_template('base.html')

@app.route("/dashboard")
def dashboard():
    entries = JournalEntry.query.order_by(JournalEntry.date.asc()).all()
    recent_entries = []

    date_now = datetime.now()
    weekly_date = (date_now - timedelta(days=7))
    monthly_date = (date_now - timedelta(days=30))
    yearly_date = (date_now - timedelta(days=365))
    win_count = 0

    yearly_entries = []
    monthly_entries = [] 
    weekly_entries = []

    chart_labels = []
    chart_values = []


    for entry in entries: 
        if entry.date >= yearly_date.date():
            yearly_entries.append(entry.pnl)
        if entry.date >= monthly_date.date():
            monthly_entries.append(entry.pnl)
            chart_labels.append(entry.date.strftime("%Y-%m-%d"))
            chart_values.append(entry.pnl)
        if entry.date >= weekly_date.date():
            weekly_entries.append(entry.pnl)
            recent_entries.append(entry)
            
    yearly_pnl = sum(yearly_entries)
    monthly_pnl = sum(monthly_entries)
    weekly_pnl = sum(weekly_entries)

    
    for entry in entries: 
        if entry.result == 'win': 
            win_count += 1
            print(win_count)
        if len(entries) > 0:
            win_rate = round((win_count / len(entries)) * 100, 2)
        else:
            win_rate = 0
    
    round(win_rate, 2)

    return render_template(
        "dashboard.html", 
        weekly_pnl=weekly_pnl, 
        monthly_pnl=monthly_pnl, 
        yearly_pnl=yearly_pnl, 
        win_rate=win_rate, 
        entries=recent_entries,
        chart_labels=chart_labels,
        chart_values=chart_values )

@app.route("/entries")
def entries():
    entries = JournalEntry.query.all()
    return render_template("entries.html", entries=entries)
   
@app.route("/new_entry", methods=['POST', 'GET'])
def new_entry():
    if request.method == 'POST':
        form_date = datetime.strptime(request.form['date'], "%Y-%m-%d").date()
        form_amount_risked = float(request.form['amount_risked'])
        form_pnl = float(request.form['pnl'])
        form_portfolio_change = float(request.form['portfolio_change'])
        form_result = request.form['result'].strip()
        form_notes = request.form['notes'].strip()
        
        new_entry = JournalEntry(
            date = form_date,
            amount_risked = form_amount_risked,
            pnl = form_pnl,
            portfolio_change = form_portfolio_change,
            result = form_result,
            notes = form_notes
        )
        try: 
            db.session.add(new_entry)
            db.session.commit()
            return redirect(url_for("entries"))
        except:
            return 'There was an issue adding your new entry.'
    return render_template("new_entry.html")

@app.route("/edit_entry/<int:entry_id>", methods=["GET", "POST"])
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
        except:
            return 'There was an issue editing your new entry.'
    return render_template("edit_entry.html", entry=entry)




@app.route('/delete_entry/<int:entry_id>', methods=["POST"])
def delete_entry(entry_id):
    entry = db.get_or_404(JournalEntry, entry_id)
    try: 
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for("entries"))
    except:
        return 'There was an issue removing your entry.'
