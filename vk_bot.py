import os
import random

import redis
import vk_api as vk
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from load_quiz import load_quiz_from_file


def create_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Показать ответ', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Мой счет', color=VkKeyboardColor.NEGATIVE)
    return keyboard


def handle_new_question_request(event, vk_api, quiz_questions_answers,
                                redis_db, keyboard):
    question_text = random.choice(list(quiz_questions_answers.keys()))
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=question_text
    )
    redis_db.set(event.user_id, question_text)


def handle_solution_attempt(event, vk_api, quiz_questions_answers,
                            redis_db, keyboard):
    user_answer = event.text
    asked_question = redis_db.get(event.user_id)
    if asked_question:
        asked_question = asked_question.decode('utf-8')
        full_answer = quiz_questions_answers[asked_question]
        short_answer = full_answer.split('.')[0].split('(')[0].strip().lower()
        if user_answer.strip().lower() == short_answer:
            message_text = 'Верно! Для следующего вопроса нажмите "Новый вопрос".'
        else:
            message_text = 'Неверно, попробуйте ещё раз.'
    else:
        message_text = 'Добрый день! Нажмите "Новый вопрос" для начала викторины.'
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=message_text
    )


def handle_show_answer(event, vk_api, quiz_questions_answers,
                               redis_db, keyboard):
    asked_question = redis_db.get(event.user_id)
    if asked_question:
        asked_question = asked_question.decode('utf-8')
        message_text = (quiz_questions_answers[asked_question].split('.')[0])
        redis_db.delete(event.user_id)
    else:
        message_text = 'Сначала получите вопрос.'
    vk_api.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=message_text
    )


def process_commands(vk_token, quiz_questions_answers, keyboard, redis_db):
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                handle_new_question_request(
                    event, vk_api, quiz_questions_answers,
                    redis_db, keyboard
                )
            elif event.text == 'Показать ответ':
                handle_show_answer(
                    event, vk_api, quiz_questions_answers,
                    redis_db, keyboard
                )
            else:
                handle_solution_attempt(
                    event, vk_api, quiz_questions_answers,
                    redis_db, keyboard
                )


def main():
    load_dotenv()
    vk_token = os.environ['VK_GROUP_TOKEN']
    redis_db_password = os.environ['REDIS_DB_PASSWORD']
    redis_db_port = os.environ['REDIS_DB_PORT']
    redis_db_host = os.environ['REDIS_DB_HOST']
    quiz_file_path = os.environ['QUIZ_FILE_PATH']
    redis_db = redis.Redis(
        host=redis_db_host, port=redis_db_port,
        password=redis_db_password
    )
    quiz_questions_answers = load_quiz_from_file(quiz_file_path)
    keyboard = create_keyboard()
    process_commands(vk_token, quiz_questions_answers, keyboard, redis_db)


if __name__ == '__main__':
    main()