from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
db = SQLAlchemy()



# Define Models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), Unique=True)
    email = db.Column(db.String(100), Unique=True)

class Language(db.Model):
    language_id = db.Column(db.Integer, primary_key=True)
    language_code = db.Column(db.String(10), nullable=False)
    language_name = db.Column(db.String(50), nullable=False)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(50), nullable=False)

class Question(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, ForeignKey('section.section_id'))
    language_id = db.Column(db.Integer, ForeignKey('language.language_id'))
    question_text = db.Column(db.Text, nullable=False)

class UserAnswer(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.user_id'))
    question_id = db.Column(db.Integer, ForeignKey('question.question_id'))
    answer_text = db.Column(db.Text)
    skipped = db.Column(db.Boolean, default=False)
    language_id = db.Column(db.Integer, ForeignKey('language.language_id'))
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

