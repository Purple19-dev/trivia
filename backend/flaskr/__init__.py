import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app, resources={'/': {'origins': '*'}})


  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Headers', 'GET, DELETE, POST, PATCH, OPTIONS')
    return response


  @app.route('/categories', methods=['GET'])
  def get_available_categories():
    categories = Category.query.all()
    categories_format = {}
    for category in categories:
      categories_format[category.id] = category.type
    return jsonify({
      'success':True,
      'categories':categories_format
    })


  @app.route('/questions', methods=['GET'])
  def get_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)
    categories = Category.query.all()
    categories_format = {category.id: category.type for category in categories}

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
    'success': True,
    'questions': current_questions,
    'total_questions': len(Question.query.all()),
    'current_category': None,
    'categories':categories_format
    })


  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)
      else:
        question.delete()
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        return jsonify({
          'success': True,
          'deleted': question_id,
          'questions': current_questions,
          'total_questions': len(Question.query.all())
        })
    except:
      abort(422)


  @app.route('/questions', methods=['POST'])
  def create_questions():
    body = request.get_json()

    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)

    try:
      question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
      'success': True,
      'created': question.id,
      'questions': current_questions,
      'total_questions': len(Question.query.all())
      })
    except:
      abort(405)


  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    data = request.get_json()
    search_term = data.get('searchTerm', '')
    try:
      selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
      paginated_questions = paginate_questions(request, selection)
      if len(selection) == 0:
        abort(404)
      else:
        search_result = {
          'success': True,
          'questions': paginated_questions,
          'total_questions': len(Question.query.all())
        }
        return jsonify(search_result)
    except:
      abort(404)


  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_questions_by_category(category_id):
    category = Category.query.filter(Category.id == category_id).one_or_none()
    selection = Question.query.filter(Question.category == category_id).all()
    total_questions = len(selection)
    paginated_questions = paginate_questions(request, selection)

    if category is None:
      abort(422)
    elif total_questions == 0:
      abort(404)
    else:
      return jsonify({
      'success': True,
      'questions': paginated_questions,
      'total_questions': total_questions,
      'current_category': category.type
    })


  @app.route('/quizzes', methods=['POST'])
  def play_quiz_game():
    quiz = request.get_json()
    quiz_category = quiz.get('quiz_category')
    prev_questions = quiz.get('previous_questions')

    if (quiz_category is None) or (prev_questions is None):
      abort(400)
    elif quiz_category['id'] == 0:
      selection = Question.query.all()
    else:
      selection = Question.query.filter_by(category=quiz_category['id']).all()

    def random_quiz():
      return selection [random.randint(0, len(selection)-1)]

    next_question = random_quiz()

    get_quiz = True

    while get_quiz:
      if next_question.id in prev_questions:
        next_question = random_quiz()
      else:
        get_quiz = False
    return jsonify({
      'success': True,
      'question': next_question.format(),
    })


  app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': "resource not found"
    }), 404

  app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': "unprocessable"
    }), 422

  app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': "method is not allowed"
    }), 405

  app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      'success': False,
      'error': 400,
      'message': 'bad request error'
    }), 400

  return app
