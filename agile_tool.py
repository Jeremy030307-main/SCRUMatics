from datetime import datetime
from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, collate, Date, Time, Float,TypeDecorator, Interval, event, and_
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timedelta
import plotly.express as px
import pandas as pd
import json
import plotly

app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

# Intermediate table for many-to-many relationship
task_labels = db.Table(
    'task_labels',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id')) ,
    db.Column('label_id', db.String(20), db.ForeignKey('label.name')))

from datetime import timedelta
from sqlalchemy.types import TypeDecorator, Interval

class Label(db.Model):
    name = db.Column(db.String(20), primary_key=True)

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    assignee = db.Column(db.String(100), nullable=False)
    story_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Define the relationship with labels using primaryjoin and secondaryjoin
    labels = relationship('Label', secondary=task_labels, backref=db.backref('tasks', lazy='dynamic'),
                            primaryjoin="Tasks.id == task_labels.c.task_id",
                            secondaryjoin="Label.name == task_labels.c.label_id")

    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    entries = db.relationship('EntryDate', backref='tasks', lazy=True)
    total_duration = db.Column(Interval)

    def edit(self, name, priority, status, category, assignee, story_points, description, labels):
        self.name = name
        self.priority = priority
        self.status = status
        self.category = category
        self.assignee = assignee
        self.story_points = story_points
        self.description = description
        self.labels = labels

class Sprints(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sprint_name = db.Column(db.Text, nullable=False)
    sprint_start_date = db.Column(db.Date, nullable=False)
    sprint_end_date = db.Column(db.Date, nullable=False)
    sprint_status = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Tasks', backref='sprints', lazy=True)

    def __init__(self, sprint_name, sprint_start_date, sprint_end_date, sprint_status):
        self.sprint_name = sprint_name
        self.sprint_start_date = sprint_start_date
        self.sprint_end_date = sprint_end_date
        self.sprint_status = sprint_status

class EntryDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    entry_time = db.relationship('EntryTime', backref='entry_date', lazy=True)
    duration = db.Column(Interval)

class EntryTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_date_id = db.Column(db.Integer, db.ForeignKey('entry_date.id'), nullable=False)  # Use 'entry_date.id' here
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    duration = db.Column(Interval)

def filter_and_sort_tasks(filter_condition=None, sort_column=None, ordering = "ascending"):
    query = Tasks.query

    if filter_condition is not None:
        query = query.filter(and_(filter_condition, Tasks.sprint_id.is_(None)))
    else:
        query = query.filter(Tasks.sprint_id.is_(None))

    if sort_column is not None:
        if ordering == "ascending":
            query = query.order_by(collate(sort_column, 'NOCASE').asc())
        else:
            query = query.order_by(collate(sort_column, 'NOCASE').desc())

    tasks = query.all()

    return tasks

@app.route('/')
def scrum_board():
    sprints = Sprints.query.all()
    return render_template('scrum_board.html', sprints = sprints)

@app.route('/product-backlog', methods = ['GET', 'POST'])
def product_backlog():

    sort_map = {
        "name" : Tasks.name,
        "priority" : Tasks.priority,
        "story_points" : Tasks.story_points,
        "created_at" : Tasks.created_at}

    proirity_map = {
        1 : "Low",
        2: "Medium",
        3: "Important", 
        4: "Urgent"}

    filter_map = {
        "Front End": Tasks.labels.any(Label.name == "Front End"),
        "Back End" : Tasks.labels.any(Label.name == "Back End"),
        "API":Tasks.labels.any(Label.name == "API"),
        "Database": Tasks.labels.any(Label.name == "Database"),
        "Framework": Tasks.labels.any(Label.name == "Framework"),
        "Testing": Tasks.labels.any(Label.name == "Testing"),
        "UI": Tasks.labels.any(Label.name == "UI"),
        "UX": Tasks.labels.any(Label.name == "UX")}

    # the default sorting element
    sorting_style, sorting_element, ordering = "default", "", ""
    tasks = None
    filter_style = 'default'
    filter_element = None
    sprint = Sprints.query.first() 

    if request.method == "POST":

        sorting_style = request.form["sorting style"] 

        try:
            filter_style = request.form["filter_element"]
            filter_element = filter_map[filter_style]
        except:   
            pass

        if sorting_style in sort_map:
            sorting_element = sort_map[sorting_style]

            try:
                ordering = request.form["ordering"]
            except:
                pass
    
    tasks = filter_and_sort_tasks(filter_element, sorting_element, ordering)

    return render_template('product_backlog.html', tasks = tasks, proirity_map = proirity_map, 
                                selected_sort = sorting_style, selected_order = ordering, selected_filter = filter_style, sprint=sprint)

@app.route('/addtask', methods = ['GET', 'POST'])
def new_task():
   if request.method == 'POST':

        this_task_labels = []
        for label in request.form.getlist("label_type[]"):

            # check is there existing label 
            existing_label = Label.query.filter_by(name=label).first()

            if existing_label:
                this_task_labels.append(existing_label)
            else:
                this_task_labels.append(Label(name = label))

        task = Tasks(
            name = request.form["task_name"],
            priority = request.form["priority_level"],
            status = request.form["status_type"],
            category = request.form["category_type"],
            assignee = request.form["assignee_name"],
            story_points = request.form['point'],
            description = request.form["task_description"],
            labels = this_task_labels
        )

        db.session.add(task)
        db.session.commit()

        return redirect(url_for('product_backlog'))
   return render_template('new_task.html')

@app.route('/addtask/<int:task_id>/edit', methods = ['GET', 'POST'])
def edit_task(task_id):

    this_task = Tasks.query.get(task_id)
    labels_name = [label.name for label in this_task.labels]

    if request.method == 'POST':
        
        this_task_labels = []
        for label in request.form.getlist("label_type[]"):
            # check is there existing label 
            existing_label = Label.query.filter_by(name=label).first()
            if existing_label:
                this_task_labels.append(existing_label)
            else:
                this_task_labels.append(Label(name = label))

        # change the task detail
        this_task.edit(
            name = request.form["task_name"],
            priority = request.form["priority_level"],
            status = request.form["status_type"],
            category = request.form["category_type"],
            assignee = request.form["assignee_name"],
            story_points = request.form['point'],
            description = request.form["task_description"],
            labels = this_task_labels
        )

        db.session.commit()

        return redirect(url_for('product_backlog'))
    return render_template('edit_task.html', task = this_task, labels = labels_name)

@app.route('/addtask/<int:task_id>', methods = ['GET', 'POST'])
def view_task(task_id):
    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]

    if request.method == "POST":

        for entry_date in this_task.entries:
            for entry_time in entry_date.entry_time:
                db.session.delete(entry_time)
            db.session.delete(entry_date)

        db.session.delete(this_task)
        db.session.commit()

        return redirect(url_for('product_backlog'))
    return render_template("view_task.html", task = this_task, labels = this_task_labels)  

@app.route('/sprint/<int:sprint_id>', methods=['GET', 'POST'])
def sprint(sprint_id):
    task_list = Tasks.query.filter(Tasks.sprint_id == sprint_id).all()

    if request.method == "POST":
        db.session.delete(this_sprint)
        db.session.commit()
        return redirect(url_for('scrum_board'))

    return render_template("sprint_backlog.html", sprint_id=sprint_id, tasks = task_list)

@app.route('/sprint/<int:sprint_id>/select-task', methods=['GET', 'POST'])
def select_task(sprint_id):

    tasks = Tasks.query.filter(Tasks.sprint_id.is_(None))
    proirity_map = {
        1 : "Low",
        2: "Medium",
        3: "Important", 
        4: "Urgent"}

    if request.method == "POST":
        task_ids = request.form.getlist("selected_tasks[]")
        for task_id in task_ids:
            task = Tasks.query.get(task_id)
            task.sprint_id = sprint_id
        
        db.session.commit()
        return redirect(url_for("sprint", sprint_id = sprint_id))
    return render_template('select_task.html', sprint_id = sprint_id, tasks=tasks, proirity_map = proirity_map)

@app.route('/newSprint', methods=['GET', 'POST'])
def new_sprint():
    if request.method == 'POST':
        sprint_name = request.form['sprint-name']
        start_date = datetime.strptime(request.form['sprint-start-date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['sprint-end-date'], '%Y-%m-%d').date()
        status = request.form['sprint-status']

        sprint = Sprints(sprint_name, start_date, end_date, status)
        db.session.add(sprint)
        db.session.commit()

        return redirect(url_for('scrum_board'))

@app.route('/hahaha/<int:task_id>')
def view_sprint_task(task_id):
    
    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]
    
    return render_template('view_sprint_task.html', task = this_task, labels = this_task_labels)

@app.route('/hahaha/<int:task_id>/log-time-spent', methods = ['GET', 'POST'])
def log_time_spent(task_id):

    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]

    if request.method == "POST":

        entry_date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(request.form["start_time"], '%H:%M')
        end_time = datetime.strptime(request.form["end_time"], '%H:%M')

        entries = [(entry_date, start_time, end_time)]
        if end_time < start_time:

            start_of_day = (start_time + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

            entries = [(entry_date, start_time, start_of_day), (entry_date + datetime.timedelta(days=1), start_of_day, end_time + datetime.timedelta(days=1))]

        for entry_date, start_time, end_time in entries:

            existing_entry_date = EntryDate.query.filter(and_(EntryDate.date==entry_date, EntryDate.task_id==task_id)).first()
            entry_date_id = None
            if existing_entry_date:
                entry_date_id = existing_entry_date.id
            else:
                existing_entry_date = EntryDate(task_id=task_id, date=entry_date)
                db.session.add(existing_entry_date)
                db.session.flush()
                entry_date_id = existing_entry_date.id

            existing_entry_time = existing_entry_date.entry_time
            overlap_time = False
            for entry_time in existing_entry_time:
                overlap_time = is_overlap(entry_time.start_time, entry_time.end_time, start_time.time(), end_time.time())

            if not overlap_time:
                time_spend = EntryTime(
                    entry_date_id = entry_date_id,
                    start_time = start_time.time(),
                    end_time = end_time.time(),
                    duration = end_time - start_time
                    )
                db.session.add(time_spend)

                if existing_entry_date.duration is None:
                    existing_entry_date.duration = end_time - start_time
                else:
                    existing_entry_date.duration += end_time - start_time

                task = Tasks.query.get(existing_entry_date.task_id)
                if task.total_duration is None:
                    task.total_duration = end_time - start_time
                else:
                    task.total_duration += end_time - start_time
            else:
                flash("Time Logged Overlap.", 'error')
            
        db.session.commit()
    
    entries_query = EntryDate.query.filter(EntryDate.task_id==task_id).order_by(EntryDate.date).all()
    
    date_list = []
    duration_list = []
    hover_text = []

    if len(entries_query) == 0 or entries_query[0].date != this_task.created_at.date():
        date_list = [this_task.created_at.date().strftime("%d-%m-%Y")]
        duration_list = [0]
        hover_text = [f"Date: {this_task.created_at.date()} <br>Task Created."]

    for entry in entries_query:
        date_list.append(entry.date.strftime("%d-%m-%Y"))
        duration_list.append(entry.duration.total_seconds()/3600)
        text = f"Date: {entry.date}<br><br>Logged Time:<br>"
        for time_period in entry.entry_time:
            text += f" • {time_period.start_time} - {time_period.end_time}<br>"
        
        hours = entry.duration.seconds // 3600
        minutes = (entry.duration.seconds // 60) % 60

        # Format the string
        formatted_time = f"{hours} hours {minutes} minutes"
        text += f"<br>Effort Per Day: {hours} hours {minutes} minutes<br>"
        hover_text.append(text)

    data = pd.DataFrame({
        'Date' : date_list, 
        'Duration' : duration_list,
        "HoverText" : hover_text })

    # Calculate cumulative sum
    data['Effort'] = data['Duration'].cumsum()

    for index, row in data.iterrows():
        accumulate_effort = row['Effort']
        data['HoverText'][index] += f"Efforts Accumulate: {int(accumulate_effort)} hours {round((accumulate_effort - int(accumulate_effort))*60) } minutes"

    fig = px.line(data, x='Date', y='Effort', title='Accumulation of Effort', hover_data='HoverText', markers=True)
    fig.update_traces(hovertemplate='%{customdata[0]}')
    max_effort = max(data['Effort'])
    fig.update_layout(yaxis=dict(range=[0, max_effort+1 if max_effort > 0 else 1]))  # Adjust the 'range' parameter

    graph_json = json.dumps(fig, cls= plotly.utils.PlotlyJSONEncoder)

    return render_template('log_time_spent.html', graphJSON=graph_json, task_id=task_id, created_date=this_task.created_at.strftime("%Y-%m-%d"))

@app.route('/clear-database', methods=['GET'])
def clear_database():
    # Drop all tables in the database
    db.drop_all()
    
    # Recreate the tables (optional, if needed)
    db.create_all()

    return 'Database cleared'

if __name__ == '__main__':
    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    app.run(debug=True)

# addtional function 
def is_overlap(range1_start, range1_end, range2_start, range2_end):
    return range1_start <= range2_end and range1_end >= range2_start

