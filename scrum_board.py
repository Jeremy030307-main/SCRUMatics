from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"


# Create the Sprint 
class Sprint(db.Model):
    sprint_name = db.Column(db.String(100), primary_key=True)
    status = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

@app.route('/', methods=['GET', 'POST'])
def main_page():
    if request.method == 'POST':
        sprint_name = request.form['sprint-name']
        date_range = request.form['sprint-date']
        status = request.form['sprint-status']

        # Split date range and parse start and end dates
        start_date_str, end_date_str = date_range.split(' - ')
        start_date = datetime.strptime(start_date_str, '%m/%d/%Y').date()
        end_date = datetime.strptime(end_date_str, '%m/%d/%Y').date()

        # Create a new Sprint object and add it to the database
        new_sprint = Sprint(sprint_name=sprint_name, start_date=start_date, end_date=end_date, status=status)
        db.session.add(new_sprint)
        db.session.commit()

    sprints = Sprint.query.all()
    return render_template('scrum_board.html', sprints=sprints)


@app.route('/clear-database', methods=['GET'])
def clear_database():
    # Drop all tables in the database
    db.drop_all()
    
    # Recreate the tables (optional, if needed)
    db.create_all()

    return 'Database cleared'

if __name__ == '__main__':
    app.run(debug=True)