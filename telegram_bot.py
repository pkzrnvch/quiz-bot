import os
import json
from enum import Enum
from functools import partial

import redis
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater,
                          CommandHandler,
                          ConversationHandler,
                          MessageHandler,
                          Filters,
                          RegexHandler)

from load_quiz import load_quizzes_from_directory_to_redis


class ConversationState(Enum):
    CHOOSING = 0
    ANSWERING = 1


REPLY_KEYBOARD = [['Новый вопрос', 'Показать ответ'], ['Мой счет']]
REPLY_MARKUP = ReplyKeyboardMarkup(REPLY_KEYBOARD)


def start(update, context):
    update.message.reply_text(
        'Добрый день! Нажмите "Новый вопрос" для начала викторины, '
        'либо введите /cancel для завершения работы.',
        reply_markup=REPLY_MARKUP
    )
    return ConversationState.CHOOSING


def cancel(update, context, redis_db):
    update.message.reply_text(
        'Завершение работы викторины.',
        reply_markup=ReplyKeyboardRemove()
    )
    user_id = update.effective_user.id
    redis_db.hdel('user_total_questions', f'user_tg_{user_id}')
    redis_db.hdel('user_correct_answers', f'user_tg_{user_id}')
    return ConversationHandler.END


def handle_new_question_request(update, context, redis_db):
    if update.message.text == 'Показать ответ':
        update.message.reply_text(
            'Вы еще не начали викторину.',
            reply_markup=REPLY_MARKUP
        )
        return ConversationState.CHOOSING
    question = redis_db.hrandfield('questions').decode('utf-8')
    question_text = json.loads(
        redis_db.hget(
            'questions',
            question
        ).decode('utf-8'))['question']
    update.message.reply_text(
        question_text,
        reply_markup=REPLY_MARKUP
    )
    user_id = update.effective_user.id
    redis_db.hset(
        'user_asked_question',
        f'user_tg_{user_id}',
        question
    )
    redis_db.hincrby('user_total_questions', f'user_tg_{user_id}', 1)
    redis_db.hset('user_correct_answers', f'user_tg_{user_id}', 0)
    return ConversationState.ANSWERING


def handle_solution_attempt(update, context, redis_db):
    user_answer = update.message.text
    user_id = update.effective_user.id
    asked_question = redis_db.hget(
        'user_asked_question',
        f'user_tg_{user_id}'
    ).decode('utf-8')
    full_answer = json.loads(
        redis_db.hget(
            'questions',
            asked_question
        ).decode('utf-8'))['answer']
    short_answer = full_answer.split('.')[0].split('(')[0].strip().lower()
    if user_answer.strip().lower() == short_answer:
        message_text = 'Верно! Для следующего вопроса нажмите "Новый вопрос".'
        update.message.reply_text(message_text, reply_markup=REPLY_MARKUP)
        redis_db.hincrby('user_correct_answers', f'user_tg_{user_id}', 1)
        return ConversationState.CHOOSING
    else:
        message_text = 'Неверно, попробуйте ещё раз.'
        update.message.reply_text(message_text)
        return ConversationState.ANSWERING


def handle_show_answer(update, context, redis_db):
    if update.message.text == 'Новый вопрос':
        update.message.reply_text(
            'Даже не посмотрите на правильный ответ? )',
            reply_markup=REPLY_MARKUP
        )
        return ConversationState.ANSWERING
    user_id = update.effective_user.id
    asked_question = redis_db.hget(
        'user_asked_question',
        f'user_tg_{user_id}'
    ).decode('utf-8')
    answer = json.loads(
        redis_db.hget(
            'questions',
            asked_question
        ).decode('utf-8'))['answer'].split('.')[0]
    update.message.reply_text(answer, reply_markup=REPLY_MARKUP)
    return ConversationState.CHOOSING


def handle_score_request(update, context, redis_db):
    user_id = update.effective_user.id
    user_total_questions = redis_db.hget(
        'user_total_questions',
        f'user_tg_{user_id}'
    ).decode('utf-8')
    user_correct_answers = redis_db.hget(
        'user_correct_answers',
        f'user_tg_{user_id}'
    ).decode('utf-8')
    message_text = f'Вопросов задано: {user_total_questions}\n'\
                   f'Правильных ответов: {user_correct_answers}'
    update.message.reply_text(message_text, reply_markup=REPLY_MARKUP)
    return ConversationState.CHOOSING


def main():
    load_dotenv()
    tg_bot_token = os.environ.get('TG_BOT_TOKEN')
    redis_db_password = os.environ['REDIS_DB_PASSWORD']
    redis_db_port = os.environ['REDIS_DB_PORT']
    redis_db_host = os.environ['REDIS_DB_HOST']
    quizzes_directory_path = os.environ['QUIZZES_DIRECTORY_PATH']
    redis_db = redis.Redis(
        host=redis_db_host, port=redis_db_port,
        password=redis_db_password
    )
    load_quizzes_from_directory_to_redis(quizzes_directory_path)
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ConversationState.CHOOSING: [
                RegexHandler(
                    '^(Новый вопрос|Показать ответ)$',
                    partial(
                        handle_new_question_request,
                        redis_db=redis_db
                    )
                ),
                RegexHandler(
                    '^(Мой счет)$',
                    partial(
                        handle_score_request,
                        redis_db=redis_db
                    )
                )
            ],
            ConversationState.ANSWERING: [
                RegexHandler(
                    '^(Новый вопрос|Показать ответ)$',
                    partial(
                        handle_show_answer,
                        redis_db=redis_db
                    )
                ),
                RegexHandler(
                    '^(Мой счет)$',
                    partial(
                        handle_score_request,
                        redis_db=redis_db
                    )
                ),
                MessageHandler(
                    Filters.text,
                    partial(
                        handle_solution_attempt,
                        redis_db=redis_db
                    )
                )
            ]
        },
        fallbacks=[CommandHandler('cancel', partial(cancel, redis_db=redis_db))]
    )
    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
