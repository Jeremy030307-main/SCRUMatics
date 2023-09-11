from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, collate
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

# Intermediate table for many-to-many relationship
task_labels = db.Table(
    'task_labels',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id')) ,
    db.Column('label_id', db.String(20), db.ForeignKey('label.name')))

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

def filter_and_sort_tasks(filter_condition=None, sort_column=None, ordering = "ascending"):
    query = Tasks.query

    if filter_condition is not None:
        query = query.filter(filter_condition)

    if sort_column is not None:
        if ordering == "ascending":
            query = query.order_by(collate(sort_column, 'NOCASE').asc())
        else:
            query = query.order_by(collate(sort_column, 'NOCASE').desc())

    tasks = query.all()

    return tasks

@app.route('/', methods = ['GET', 'POST'])
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
                                selected_sort = sorting_style, selected_order = ordering, selected_filter = filter_style)

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