from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import random
from enum import Enum
from Question import SECTION
from sqlalchemy import Enum as SQLAlchemyEnum
from flask import g


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
db = SQLAlchemy(app)

from enum import Enum

class LanguageEnum(Enum):
    ENGLISH = 'english'
    FRENCH = 'french'
    GERMAN = 'german'
    SPANISH = 'spanish'

class Language(db.Model):
    language_id = db.Column(db.Integer, primary_key=True)
    language_name = db.Column(db.Enum(LanguageEnum), nullable=False, default=LanguageEnum.ENGLISH.value)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)

class Section(db.Model):
    section_id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(50),  unique=True)   

class Question(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.section_id'))
    question_text = db.Column(db.Text, nullable=False)
    is_accessible_to_v7 = db.Column(db.Boolean, default=False)  


class UserAnswer(db.Model):
    answer_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.user_id'))
    question_id = db.Column(db.Integer, ForeignKey('question.question_id'))
    answer_text = db.Column(db.Text)
    skipped = db.Column(db.Boolean, default=False)
    language_id = db.Column(db.Integer, ForeignKey('language.language_id'))
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())


class QuestionLanguage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.question_id'))
    language_id = db.Column(db.Integer, db.ForeignKey('language.language_id'))
    question_text = db.Column(db.Text, nullable=False)





@app.route('/api/questions/<int:section_id>', methods=['GET'])
def get_questions(section_id):
    """
    API Endpoint for Retrieving Unanswered Questions: 
    This endpoint handles HTTP GET requests to retrieve the first unanswered question from a specific section. 
    It dynamically fetches questions based on section ID and optionally user ID.

    Parameters:
    - section_id (integer): Unique identifier of the section to retrieve questions from.
    - user_id (optional, string): Identifier of the user to check for answered questions. 
      If provided, the endpoint returns the first unanswered question for this user. 
      If not, it returns the first unanswered question in the section.

    Returns:
    - JSON Response: Contains details of the retrieved question or a message indicating the absence 
      of unanswered questions in the specified section.

    Example Request:
    GET /api/questions/1234?user_id=5678

    Example Response:
    {
        "section_name": "Example Section",
        "question_id": 9876,
        "question_text": "What is the capital of France?"
    }
    Note:
    - For the "V7" section, this endpoint returns the first unanswered question from any section. 
      "V7" has access to all questions from different sections.
    """

    # Get the section information from the database
    section = Section.query.get(section_id)
    
    if not section:
        return jsonify({"error": "Section not found"}), 404

    section_name = section.section_name

    # Get the user ID from the request parameters
    user_id = request.args.get("user_id")

    # Fetch the answered question IDs for the user
    if user_id:
        answered_question_ids = [answer.question_id for answer in UserAnswer.query.filter_by(user_id=user_id).all()]
    else:
        answered_question_ids = []

    questions = []

    if section_name == "V7":
        # "V7" section can access all questions from different sections
        questions = Question.query.all()
    else:
        # Retrieve questions only for the specific section
        questions = Question.query.filter_by(section_id=section_id).all()

    # Find the first unanswered question in the section
    for question in questions:
        if question.question_id not in answered_question_ids:
            return jsonify({
                "section_name": section_name,
                "question_id": question.question_id,
                "question_text": question.question_text
            })

    return jsonify({"message": f"No more unanswered questions in the {section_name} section"})














@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
def delete_question(question_id):
    """
    API Endpoint for Deleting a Question from All Languages: This endpoint handles HTTP DELETE requests to delete a question from all languages.
    
    Parameters:
    - question_id (integer): The ID of the question to be deleted.
    
    Returns:
    - JSON Response: Indicates whether the question was deleted successfully or if there was an error.
    """
    # Check if the question exists
    question = Question.query.get(question_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    # Delete the question from all languages
    deleted_question_count = QuestionLanguage.query.filter_by(question_id=question_id).delete()
    db.session.commit()

    return jsonify({"message": f"{deleted_question_count} question(s) deleted from all languages"}), 200











@app.route('/change-language', methods=['POST'])
def change_language():
    """
    API Endpoint for Changing User's Selected Language: This endpoint handles HTTP POST requests to change the selected language of a user.
    
    Parameters:
    - user_id (integer): The ID of the user whose language needs to be updated.
    - language_id (integer): The ID of the language to set as the user's selected language.
    
    Returns:
    - JSON Response: Indicates whether the language was updated successfully or if there was an error.
    """
    data = request.json
    if not all(key in data for key in ['user_id', 'language_id']):
        return jsonify({'error': 'Invalid request'}), 400
    
    user_id = data['user_id']
    language_id = data['language_id']

    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if language ID is valid
    if not Language.query.filter_by(language_id=language_id).first():
        return jsonify({'error': 'Invalid language ID'}), 400

    # Update user's selected language
    user.selected_language = language_id
    db.session.commit()

    return jsonify({'message': 'Language updated successfully'}), 200







@app.route('/api/answers', methods=['POST'])
def submit_answer():
    data = request.json
    user_id = data.get("user_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text")

        
    ''' API Endpoint for Submitting Answers: This endpoint handles HTTP POST requests to submit answers to questions.
    Parameters:
    - request: The HTTP request object containing the data to be processed.
    Returns:
    - JSON Response: An appropriate JSON response based on the success or failure of the data processing.
    Example:
    POST /api/answers/
    {
    "user_id": "123",
    "question_id": "456",
    "answer_text": "Paris"
    }
    The above request triggers this post method, processing the data and returning a relevant response.
    '''
    if not user_id or not question_id or not answer_text:
        return jsonify({"error": "Missing required parameters"}), 400

    user_answer = UserAnswer(user_id=user_id, question_id=question_id, answer_text=answer_text)
    db.session.add(user_answer)
    db.session.commit()

    return jsonify({"message": "Answer submitted successfully"})





@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_answer_history(user_id):
    ''' API Endpoint for Retrieving Answer History: This endpoint handles HTTP GET requests to retrieve the answer history of a user.
    Parameters:
    - user_id (integer): The unique identifier of the user whose answer history is to be retrieved.
    Returns:
    - JSON Response: Contains the answer history of the specified user.
    Example Request:
    GET /api/history/123
    Example Response:
    {
    "user_id": 123,
    "history": [
        {
        "question_id": 1,
        "question_text": "What is the capital of France?",
        "answer_text": "Paris",
        "skipped": false,
        "timestamp": "2024-02-05 10:30:00"
        },
        {
        "question_id": 2,
        "question_text": "What is the capital of Italy?",
        "answer_text": "Rome",
        "skipped": true,
        "timestamp": "2024-02-05 10:35:00"
        }
    ]
    }
    '''
    user_history = UserAnswer.query.filter_by(user_id=user_id).all()
    history_data = []    
    for answer in user_history:
        question_text = Question.query.filter_by(question_id=answer.question_id).first().question_text
        history_data.append({
            "question_id": answer.question_id,
            "question_text": question_text,
            "answer_text": answer.answer_text,
            "skipped": answer.skipped,
            "timestamp": answer.timestamp
        })

    return jsonify({"user_id": user_id, "history": history_data})














@app.route('/api/v7', methods=['GET'])
def get_v7_questions():
        
    ''' API Endpoint for Retrieving V7 Questions: This endpoint handles HTTP GET requests to retrieve questions from category V7.
    Parameters: None
    Returns:
    - JSON Response: Contains the questions from category V7.
    Example Request:
    GET /api/v7
    Example Response:
    {
    "category": "V7",
    "questions": [
        {
        "question_id": 1,
        "question_text": "What is the meaning of life?"
        },
        {
        "question_id": 2,
        "question_text": "What is the airspeed velocity of an unladen swallow?"
        }
    ]
    }
    '''
    v7_questions = SECTIONS.get("V7", [])
    return jsonify({"category": "V7", "questions": v7_questions})



@app.route('/api/v7/answer', methods=['POST'])
def submit_v7_answer():
    '''
    API Endpoint for Submitting V7 Answers: This endpoint handles HTTP POST requests to submit answers to questions in category V7.
    Parameters:
    - request: The HTTP request object containing the data to be processed.
    Returns:
    - JSON Response: An appropriate JSON response based on the success or failure of the data processing.
    Example:
    POST /api/v7/answer/
    {
    "user_id": "123",
    "question_id": "2",
    "answer_text": "42"
    }
    The above request triggers this post method, processing the data and returning a relevant response.

    '''

    data = request.json
    user_id = data.get("user_id")
    question_id = data.get("question_id")
    answer_text = data.get("answer_text")

    if not user_id or not question_id or not answer_text:
        return jsonify({"error": "Missing required parameters"}), 400

    allowed_sequence = [2, 4, 5]
    if question_id not in allowed_sequence:
        return jsonify({"error": "Invalid question_id for the V7 section"}), 400

    user_answer = UserAnswer(user_id=user_id, question_id=question_id, answer_text=answer_text)
    db.session.add(user_answer)
    db.session.commit()

    return jsonify({"message": "Answer submitted successfully"})



@app.route('/api/sections', methods=['GET'])
def get_sections():
    
    """
    API Endpoint for Retrieving All Sections: This endpoint handles HTTP GET requests to retrieve all sections available.
    
    Parameters: None
    
    Returns:
    - JSON Response: Contains details of all sections including section ID and section name.
    
    Example Request:
    GET /api/sections
    
    Example Response:
    {
      "sections": [
        {
          "section_id": 1,
          "section_name": "Science"
        },
        {
          "section_id": 2,
          "section_name": "History"
        }
      ]
    }
    """

    all_sections = Section.query.all()
    sections_data = [{"section_id": section.section_id, "section_name": section.section_name} for section in all_sections]
    return jsonify({"sections": sections_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
