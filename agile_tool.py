from datetime import datetime
from flask import Flask, render_template, request, session, flash, redirect, url_for, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, collate, Date, Time, Float,TypeDecorator, Interval, event, and_, nulls_last, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timedelta
import plotly.express as px
import pandas as pd
import json
import plotly
from sqlalchemy.types import TypeDecorator, Interval
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import math


app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "random string"
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'

# Intermediate table for many-to-many relationship
task_labels = db.Table(
    'task_labels',
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id')) ,
    db.Column('label_id', db.String(20), db.ForeignKey('label.name')))

roles_users = db.Table( 'roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(50), nullable = False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('user', lazy='dynamic'))
    tasks = db.relationship('Tasks', backref='user', lazy=True)
    entries = db.relationship('EntryDate', backref='user', lazy=True)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(40))
    description = db.Column(db.String(225))

class Label(db.Model):
    name = db.Column(db.String(20), primary_key=True)

class Tasks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    assignee = db.Column(db.Integer, db.ForeignKey('user.id'))
    story_points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Define the relationship with labels using primaryjoin and secondaryjoin
    labels = relationship('Label', secondary=task_labels, backref=db.backref('tasks', lazy='dynamic'),
                            primaryjoin="Tasks.id == task_labels.c.task_id",
                            secondaryjoin="Label.name == task_labels.c.label_id")

    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id'))
    entries = db.relationship('EntryDate', backref='tasks', lazy=True)
    completion_date = db.Column(db.DateTime(timezone=True))

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duration = db.Column(Interval)

class EntryTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_date_id = db.Column(db.Integer, db.ForeignKey('entry_date.id'), nullable=False)  # Use 'entry_date.id' here
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=True)
    duration = db.Column(Interval)

class MyModelView(ModelView):

    def is_accessible(self):
        return Role.query.get(1) in current_user.roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class CustomAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        record_count = len(User.query.all())
        print(record_count)
        return self.render('admin/index.html', number_of_members=record_count)

class TeamEffortView(BaseView):
    @expose('/')

    def index(self):
        start_date = session.get('start_date', None)
        end_date = session.get('end_date', None)

        if start_date is None or end_date is None:
            pass
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            period = (end_date - start_date).days

            users = User.query.all()
            entries_date = EntryDate.query.all()
            user_entry_dict = {}

            for user in users:
                user_entry_dict[user] = EntryDate.query.filter(EntryDate.user_id==user.id).all()

            user_data = [user.username for user in users]
            hover_text = []
            user_effort_data = []
            for user in users:
                user_entries = user_entry_dict[user]
                total=timedelta()
                for entry in user_entries:
                    if start_date <= entry.date <= end_date:
                        total += entry.duration

                average_second = total.total_seconds()/period
                user_effort_data.append(round(average_second/3600,2))

                hours = average_second // 3600
                minutes = (average_second // 60) % 60
                hover_text.append(f"{user.username} worked average of {hours} hours {minutes} minutes.")

            data = pd.DataFrame({
                'User' : user_data, 
                'Duration(hours)' : user_effort_data,
                'hover_text': hover_text
                })

            fig = px.bar(data, x='User', y='Duration(hours)', hover_data='hover_text', title="Average Time Spend Per Day (" + start_date.strftime("%Y-%m-%d") + " - " + end_date.strftime("%Y-%m-%d") + ")")
            graph_json = json.dumps(fig, cls= plotly.utils.PlotlyJSONEncoder)

            return self.render('admin/team_statistic.html', graphJSON = graph_json, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
        return self.render('admin/team_statistic.html')

    @app.route('/handle-contribution-form', methods = ["POST", "GET"])
    def handle_contribution_form():
        if request.method == "POST":
            session["start_date"] = request.form["startDate"]
            session["end_date"] = request.form["endDate"]
            return redirect(url_for('team-contribution.index'))

admin = Admin(app, base_template='admin/navbar_less_base.html', template_mode='bootstrap3', index_view=CustomAdminIndexView())
admin.add_view(MyModelView(User, db.session))
admin.add_view(TeamEffortView(name='Team Contribution', endpoint='team-contribution'))

# Define an event listener that triggers when 'your_column' changes
@event.listens_for(Tasks.status, 'set')
def task_complete_listner(target, value, oldvalue, initiator):
    specific_value = 'completed'
    if value == specific_value:
        # Update 'timestamp_column' with the current timestamp
        target.completion_date = datetime.utcnow()
    else:
        target.completion_date = None

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
########################################## ------- Route ------- ##########################################################

# --------------------------------------------- login/logout ------------------------------------------------------------
@app.route('/')
def main():
    logout_user()
    return render_template('login.html')

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method=="POST":
        user = User.query.filter_by(username=request.form['username']).first()
        if user:
            if request.form['password'] == user.password:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('scrum_board'))
            else:
                flash('Invalid password. Please try again.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main'))

# ------------------------------------------------------- main page --------------------------------------------------------
@app.route('/scrum-board')
@login_required
def scrum_board():
    sprints = Sprints.query.all()
    return render_template('scrum_board.html', sprints = sprints)

# ------------------------------------------------------- product backlog ----------------------------------------------
@app.route('/product-backlog', methods = ['GET', 'POST'])
@login_required
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

# ----------------------------------------------------- task related route ----------------------------------------------------
@app.route('/addtask', methods = ['GET', 'POST'])
@login_required
def new_task():

    team_member = User.query.all()

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

    return render_template('new_task.html', team = team_member)

@app.route('/addtask/<int:task_id>/edit', methods = ['GET', 'POST'])
@login_required
def edit_task(task_id):

    this_task = Tasks.query.get(task_id)
    labels_name = [label.name for label in this_task.labels]
    team_member = User.query.all()

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

        sprint_id = this_task.sprint_id

        db.session.commit()
        if sprint_id is None:
            return redirect(url_for('product_backlog'))
        else:
            return redirect(url_for('sprint', sprint_id = sprint_id))

    return render_template('edit_task.html',team = team_member, task = this_task, labels = labels_name)

@app.route('/addtask/<int:task_id>', methods = ['GET', 'POST'])
@login_required
def view_task(task_id):
    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]
    team_member = User.query.all()

    if request.method == "POST":

        for entry_date in this_task.entries:
            for entry_time in entry_date.entry_time:
                db.session.delete(entry_time)
            db.session.delete(entry_date)

        sprint_id = this_task.sprint_id

        db.session.delete(this_task)
        db.session.commit()

        if sprint_id is None:
            return redirect(url_for('product_backlog'))
        else:
            return redirect(url_for('sprint', sprint_id = sprint_id))

        return redirect(url_for('product_backlog'))
        
    return render_template("view_task.html",team = team_member, task = this_task, labels = this_task_labels)  

# --------------------------------------------------- sprint related route -------------------------------------------------
@app.route('/sprint/<int:sprint_id>', methods=['GET', 'POST'])
@login_required
def sprint(sprint_id):
    current_sprint = Sprints.query.get(sprint_id)
    task_list = Tasks.query.filter(Tasks.sprint_id == sprint_id).all()
    this_sprint = Sprints.query.get(sprint_id)
    if request.method == "POST":
        current_sprint.sprint_status = request.form["sprint_status"]
        db.session.commit()

    return render_template("sprint_backlog.html", sprint=current_sprint, tasks = task_list)

@app.route('/sprint/<int:sprint_id>/select-task', methods=['GET', 'POST'])
@login_required
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
@login_required
def new_sprint():
    if request.method == 'POST':
        current_date = datetime.now().date()
        sprint_name = request.form['sprint-name']
        start_date = datetime.strptime(request.form['sprint-start-date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['sprint-end-date'], '%Y-%m-%d').date()
        status = request.form['sprint-status']


        # Date validation: Check if the start date is not earlier than the current date
        if start_date < current_date:
            flash('Start date cannot be earlier than the current date','error')
            return redirect(url_for('scrum_board'))
        # Date validation: Check if the end date is after the start date
        elif end_date <= start_date:
            flash('Start date must be before the end date','error')
            return redirect(url_for('scrum_board'))

        
        sprint = Sprints(sprint_name, start_date, end_date, status)
        db.session.add(sprint)
        db.session.commit()

        return redirect(url_for('scrum_board'))

@app.route('/sprint/<int:sprint_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sprint(sprint_id):
  sprint = Sprints.query.get(sprint_id)

  if request.method == 'POST':
    if request.form.get('delete_sprint'):
      # Delete the sprint
      Tasks.query.filter_by(sprint_id=sprint_id).update({'sprint_id': None})
      db.session.delete(sprint)
      db.session.commit()

      return redirect(url_for('product_backlog'))

    # Update the sprint
    sprint.sprint_name = request.form['sprint_name']
    sprint.sprint_start_date = datetime.strptime(request.form['sprint_start_date'], '%Y-%m-%d').date()
    sprint.sprint_end_date = datetime.strptime(request.form['sprint_end_date'], '%Y-%m-%d').date()

    # Get the sprint status from the request form, or use a default value if the field is not present

    # Prevent users from changing a sprint status back to "Not Started" if the sprint has already been started
    # if sprint.is_started() and sprint_status == "Not Started":
    #   raise ValidationError("Cannot change sprint status back to 'Not Started' if sprint has already been started.")

    db.session.commit()

    return redirect(url_for('scrum_board'))

  return render_template('edit_sprint.html', sprint=sprint)

@app.route('/sprint/<int:sprint_id>/task/<int:task_id>')
@login_required
def view_sprint_task(sprint_id, task_id):
    
    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]
    team_member = User.query.all()
    
    return render_template('view_sprint_task.html', sprint_id=sprint_id, task = this_task, labels = this_task_labels, team = team_member)

# -------------------------------------------  log time spent ---------------------------------------------------
@app.route('/sprint/<int:sprint_id>/task/<int:task_id>/log-time', methods = ['GET', 'POST'])
@login_required
def log_time_spent(sprint_id, task_id):

    this_task = Tasks.query.get(task_id)
    this_task_labels = [label.name for label in this_task.labels]

    if request.method == "POST":

        if (this_task.assignee != current_user.id):
            flash(f"This task is assign to {User.query.get(this_task.assignee).username}", "error")

        else:
            entry_date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
            start_time = datetime.strptime(request.form["start_time"], '%H:%M')
            end_time = datetime.strptime(request.form["end_time"], '%H:%M')

            entries = [(entry_date, start_time, end_time)]
            if end_time < start_time:

                start_of_day = (start_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

                entries = [(entry_date, start_time, start_of_day), (entry_date + timedelta(days=1), start_of_day, end_time + timedelta(days=1))]

            for entry_date, start_time, end_time in entries:

                existing_entry_date = EntryDate.query.filter(and_(EntryDate.date==entry_date, EntryDate.task_id==task_id)).first()
                entry_date_id = None
                if existing_entry_date:
                    entry_date_id = existing_entry_date.id
                else:
                    existing_entry_date = EntryDate(task_id=task_id, date=entry_date, user_id=this_task.assignee)
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

    return render_template('log_time_spent.html', sprint_id=sprint_id, graphJSON=graph_json, task_id=task_id, created_date=this_task.created_at.strftime("%Y-%m-%d"))

# -------------------------------------------- burndown chart ------------------------------------------------------
@app.route('/sprint/<int:sprint_id>/burndown-chart')
@login_required
def burndown_chart(sprint_id):

    current_sprint = Sprints.query.get(sprint_id)
    sprint_task = Tasks.query.filter(Tasks.sprint_id == sprint_id).order_by(nulls_last(Tasks.completion_date.asc()))

    # get the total story point of the sprint
    total_story_point = 0
    for task in sprint_task:
        total_story_point += task.story_points

    # get the start and end date of the sprint
    start_date = current_sprint.sprint_start_date
    end_date = current_sprint.sprint_end_date
    
    # store the data for ideal velocity in lists
    story_point_data = [total_story_point, 0, total_story_point]
    date_data = [start_date, end_date, start_date]
    line_type = ["Ideal Velocity", "Ideal Velocity", "Actual Velocity" ]

    accumulate_story_points = total_story_point
    for task in sprint_task:
        if task.completion_date is None:
            break
        accumulate_story_points -= task.story_points
        story_point_data.append(accumulate_story_points)
        date_data.append(task.completion_date)
        line_type.append("Actual Velocity")
    
    data = pd.DataFrame({
        'Date' : date_data, 
        'Story Point' : story_point_data,
        "velocity_type" : line_type })

    print(date_data)
    print(story_point_data)
    fig = px.line(data, x='Date', y='Story Point', color="velocity_type", title='Burndown Chart of Sprint: ' + current_sprint.sprint_name, markers=True)
    graph_json = json.dumps(fig, cls= plotly.utils.PlotlyJSONEncoder)
    return render_template('burndown_chart.html', graphJSON=graph_json)

# -------------------------------------------- developer route -----------------------------------------------------------
@app.route('/clear-database', methods=['GET'])
def clear_database():
    # Drop all tables in the database
    db.drop_all()
    
    # Recreate the tables (optional, if needed)
    db.create_all()

    return 'Database cleared'

@app.route('/add-admin')
def add_admin():
    admin_role = Role(
        name = 'Admin',
        description = "Control the flow of agile process. "
    )
    db.session.add(admin_role)
    
    admin_user = User(
        username = "Admin", 
        password = "12345678",
        roles = [admin_role]
    )
    db.session.add(admin_user)
    db.session.commit()
    return "Admin Added"

@app.route("/update_task_status/<int:task_id>", methods=["POST"])
def update_task_status(task_id):
    new_status = request.json["newStatus"]
    
    this_task = Tasks.query.get(task_id)
    this_task.status = new_status
    db.session.commit()
    # Update the task status in your database (e.g., using SQLAlchemy)
    # Replace this with your actual code to update the task status

    # Return a response to the client (you can customize the response based on success/failure)
    response_data = {"message": "Task status updated successfully"}
    return jsonify(response_data)

# ------------------------------------------------user profile---------------------------------------------------------
@app.route('/user_profile', methods=['GET', 'POST'])
@login_required
def uesr_profile():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        # Check if the old password matches the one stored in the database
        if current_user.password == old_password:
            # Update the password in the database
            current_user.password = new_password
            db.session.commit()
            flash('Password changed successfully', 'success')
        else:
            flash('Invalid old password', 'error')

    return render_template("user_profile.html")

# ---------------------------------------------addtional function-------------------------------------------------------
def is_overlap(range1_start, range1_end, range2_start, range2_end):
    return range1_start <= range2_end and range1_end >= range2_start

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

if __name__ == '__main__':
    with app.app_context():
        # Create the database tables if they don't exist
        db.create_all()

    app.run(debug=True)
