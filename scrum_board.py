from datetime import datetime
from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, func, CheckConstraint, Enum

app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

class Sprints(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sprint_name = db.Column(db.Text, nullable=False)
    sprint_start_date = db.Column(db.Date, nullable=False)
    sprint_end_date = db.Column(db.Date, nullable=False)
    sprint_status = db.Column(db.String(100), nullable=False)

    # tasks = db.relationship('Tasks', backref='Sprints', lazy=True)

    def __init__(self, sprint_name, sprint_start_date, sprint_end_date, sprint_status):
        self.sprint_name = sprint_name
        self.sprint_start_date = sprint_start_date
        self.sprint_end_date = sprint_end_date
        self.sprint_status = sprint_status

@app.route('/')
def main_page():
    return render_template('scrum_board.html')

@app.route('/newSprint', methods=['GET', 'POST'])
def new_sprint():
    if request.method == 'POST':
        sprint_name = request.form['sprint-name']
        # date_range = request.form['sprint-date']
        start_date = request.form['sprint-start-date']
        end_date = request.form['sprint-end-date']
        # sprint_status = request.form["sprint-status"]

        # Split date range and parse start and end dates
        # start_date_str =  start_date.split(' - ')
        # end_date_str = end_date.split(' - ')
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()


        sprint = Sprints(sprint_name, start_date, end_date, "not started")
        db.session.add(sprint)
        db.session.commit()

        return redirect(url_for('main_page'))

if __name__ == '__main__':
    app.run(debug=True)