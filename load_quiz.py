import os
import json
from pathlib import Path

import redis
from dotenv import load_dotenv


def load_quizzes_from_directory_to_redis(quizzes_directory_path):
    load_dotenv()
    redis_db_password = os.environ['REDIS_DB_PASSWORD']
    redis_db_port = os.environ['REDIS_DB_PORT']
    redis_db_host = os.environ['REDIS_DB_HOST']
    redis_db = redis.Redis(
        host=redis_db_host, port=redis_db_port,
        password=redis_db_password
    )
    quizzes_directory_path = Path(quizzes_directory_path)
    questions_and_answers = []
    for quiz_file_path in quizzes_directory_path.iterdir():
        with open(quiz_file_path, 'r', encoding='KOI8-R') as quiz_file:
            contents = quiz_file.read()
        text_blocks = contents.split('\n\n')
        question_text = ''
        for text_block in text_blocks:
            text_block = text_block.strip()
            if text_block.startswith('Вопрос'):
                question_text = text_block.split('\n', 1)[1].replace('\n', ' ')
            elif text_block.startswith('Ответ:'):
                answer_text = text_block.split('\n', 1)[1].replace('\n', ' ')
                question_and_answer = {
                    'question': question_text,
                    'answer': answer_text
                }
                question_and_answer_json = json.dumps(question_and_answer)
                questions_and_answers.append(question_and_answer_json)
    redis_questions_and_answers = {}
    for index, question_and_answer_json in enumerate(questions_and_answers):
        key = f'question{index}'
        redis_questions_and_answers[key] = question_and_answer_json
    redis_db.hset('questions', mapping=redis_questions_and_answers)
