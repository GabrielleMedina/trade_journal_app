from flask import Flask, render_template, url_for, request, redirect
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trade.db'
db = SQLAlchemy(app)

class JournalEntry(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.now)
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
    return render_template("dashboard.html")

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
