from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, func, CheckConstraint, Enum

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

class Tasks(db.Model):

    priority_enum = Enum("low", "medium", "important", "urgent")
    status_enum = Enum("not started", "incomplete", "completed")
    category_enum = Enum("story", "bug")
    labels_enum = Enum("front end", "back end", "api", "database", "framework", "testing", "ui", "ux")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(100),nullable=False)
    status = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    labels = db.Column(db.String(100), nullable=False)
    assignee = db.Column(db.String(100), nullable=False)
    story_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    sprint_belong = db.Column(db.Integer)

    def __init__(self, name, priority, status, category, labels,assignee, story_points, description):
        self.name = name
        self.priority = priority
        self.status = status
        self.category = category
        self.labels = labels
        self.assignee = assignee
        self.story_points = story_points
        self.description = description

@app.route('/')
def product_backlog():
    return render_template('product_backlog.html', tasks = Tasks.query.all() )

@app.route('/addtask', methods = ['GET', 'POST'])
def new_task():
   if request.method == 'POST':
    
        task = Tasks(request.form['task_name'], request.form['priority_level'],
        request.form['status_type'], request.form['category_type'], request.form['label_type'], 
        request.form['assignee_name'], request.form['point'], request.form['task_description'])

        db.session.add(task)
        db.session.commit()

        flash('Task was successfully added')
        return redirect(url_for('product_backlog'))
   return render_template('new_task.html')

@app.route('/clear-database', methods=['GET'])
def clear_database():
    # Drop all tables in the database
    db.drop_all()
    
    # Recreate the tables (optional, if needed)
    db.create_all()

    return 'Database cleared'

if __name__ == '__main__':
    app.run(debug=True)