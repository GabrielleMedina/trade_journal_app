from flask import Flask, render_template, url_for
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
    result = db.Column(db.String(20), default = 0)
    notes = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<JournalEntry %r>' % self.id
    

@app.route("/")
def index():
    return render_template('base.html')
    

if __name__ == "__main__":
    app.run(debug=True)