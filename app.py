from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from Question import SECTIONS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'

db = SQLAlchemy(app)

# Define Models
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)

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


# Routes
# Routes
@app.route('/api/questions/<int:section_id>', methods=['GET'])
def get_section_questions(section_id):
    section = SECTIONS.get(section_id)
    if not section:
        return jsonify({"error": "Section not found"}), 404

    section_name = section.get("section_name")
    if not section_name:
        return jsonify({"error": "Section name not found for the section"}), 404

    return jsonify({"section_name": section_name, "questions": section["questions"]})

@app.route('/api/answers', methods=['POST'])
def submit_answer():
    data = request.json
    user_id = data.get("user_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text")

    if not user_id or not question_id or not answer_text:
        return jsonify({"error": "Missing required parameters"}), 400

    answer = {
        "user_id": user_id,
        "question_id": question_id,
        "answer_text": answer_text
    }
    answers.append(answer)

    return jsonify({"message": "Answer submitted successfully"})

@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_answer_history(user_id):
    user_history = [answer for answer in answers if answer["user_id"] == user_id]
    return jsonify(user_history)

@app.route('/api/v7', methods=['GET'])
def get_v7_questions():
    v7_questions = SECTIONS.get("V7", [])
    return jsonify({"category": "V7", "questions": v7_questions})

@app.route('/api/v7/answer', methods=['POST'])
def submit_v7_answer():
    data = request.json
    user_id = data.get("user_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text")

    if not user_id or not question_id or not answer_text:
        return jsonify({"error": "Missing required parameters"}), 400

    allowed_sequence = [2, 4, 5]
    if question_id not in allowed_sequence:
        return jsonify({"error": "Invalid question_id for the V7 section"}), 400

    answer = {
        "user_id": user_id,
        "question_id": question_id,
        "answer_text": answer_text
    }
    answers.append(answer)

    return jsonify({"message": "Answer submitted successfully"})

# New route to get sections
@app.route('/api/sections', methods=['GET'])
def get_sections():
    all_sections = Section.query.all()
    sections_data = [{"section_id": section.section_id, "section_name": section.section_name} for section in all_sections]
    return jsonify({"sections": sections_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)