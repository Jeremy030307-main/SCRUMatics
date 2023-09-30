from datetime import datetime
from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, collate
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

app = Flask(__name__, static_folder='static')
app.config['FAVICON'] = 'static/favicon.ico'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = "random string"

@app.route('/',methods=['GET', 'POST'])
def main_page():
    return render_template('product_backlog.html')

if __name__ == '__main__':
    app.run(debug=True)
