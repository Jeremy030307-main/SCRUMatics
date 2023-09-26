from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, collate
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sprints.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

@app.route('/', methods = ['GET', 'POST'])
def main_page():
    return render_template('scrum_board.html')



# create task
class Sprints(db.Model):
    sprint_name = db.Column(db.String(100), primary_key=True)
    status = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime(timezone=True))
    end_date = db.Column(db.DateTime(timezone=True))

    def edit(self, sprint_name, status, start_date, end_date):
        self.sprint_name = sprint_name
        self.status = status
        self.start_date = start_date
        self.end_date = end_date

# def filter_and_sort_tasks(filter_condition=None, sort_column=None, ordering = "ascending"):
#     query = Sprints.query

#     if filter_condition is not None:
#         query = query.filter(filter_condition)

#     if sort_column is not None:
#         if ordering == "ascending":
#             query = query.order_by(collate(sort_column, 'NOCASE').asc())
#         else:
#             query = query.order_by(collate(sort_column, 'NOCASE').desc())

#     tasks = query.all()

#     return tasks

# @app.route('/', methods = ['GET', 'POST'])
# def product_backlog():

#     sort_map = {
#         "name" : Tasks.name,
#         "priority" : Tasks.priority,
#         "story_points" : Tasks.story_points,
#         "created_at" : Tasks.created_at}

#     proirity_map = {
#         1 : "Low",
#         2: "Medium",
#         3: "Important", 
#         4: "Urgent"}

#     filter_map = {
#         "Front End": Tasks.labels.any(Label.name == "Front End"),
#         "Back End" : Tasks.labels.any(Label.name == "Back End"),
#         "API":Tasks.labels.any(Label.name == "API"),
#         "Database": Tasks.labels.any(Label.name == "Database"),
#         "Framework": Tasks.labels.any(Label.name == "Framework"),
#         "Testing": Tasks.labels.any(Label.name == "Testing"),
#         "UI": Tasks.labels.any(Label.name == "UI"),
#         "UX": Tasks.labels.any(Label.name == "UX")}
    

#     # the default sorting element
#     sorting_style, sorting_element, ordering = "default", "", ""
#     tasks = None
#     filter_style = 'default'
#     filter_element = None

#     if request.method == "POST":

#         sorting_style = request.form["sorting style"] 

#         try:
#             filter_style = request.form["filter_element"]
#             filter_element = filter_map[filter_style]
#         except:   
#             pass

#         if sorting_style in sort_map:
#             sorting_element = sort_map[sorting_style]

#             try:
#                 ordering = request.form["ordering"]
#             except:
#                 pass
    
#     tasks = filter_and_sort_tasks(filter_element, sorting_element, ordering)

#     return render_template('product_backlog.html', tasks = tasks, proirity_map = proirity_map, 
#                                 selected_sort = sorting_style, selected_order = ordering, selected_filter = filter_style)

@app.route('/addtask', methods = ['GET', 'POST'])
def new_task():
   if request.method == 'POST':
        sprint = Sprints(
            name = request.form["task_name"],
            priority = request.form["priority_level"],
            status = request.form["status_type"],
            category = request.form["category_type"],
            assignee = request.form["assignee_name"],
            story_points = request.form['point'],
            description = request.form["task_description"],
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

# @app.route('/addtask/<int:task_id>', methods = ['GET', 'POST'])
# def view_task(task_id):
#     this_task = Tasks.query.get(task_id)
#     this_task_labels = [label.name for label in this_task.labels]

#     if request.method == "POST":

#         db.session.delete(this_task)
#         db.session.commit()

#         return redirect(url_for('product_backlog'))
#     return render_template("view_task.html", task = this_task, labels = this_task_labels)

@app.route('/clear-database', methods=['GET'])
def clear_database():
    # Drop all tables in the database
    db.drop_all()
    
    # Recreate the tables (optional, if needed)
    db.create_all()

    return 'Database cleared'

if __name__ == '__main__':
    app.run(debug=True)