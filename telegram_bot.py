import os
import random
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

from load_quiz import load_quizzes_from_directory


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


def cancel(update, context):
    update.message.reply_text(
        'Завершение работы викторины.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle_new_question_request(update, context, redis_db, quiz_questions_answers):
    if update.message.text == 'Показать ответ':
        update.message.reply_text(
            'Вы еще не начали викторину.',
            reply_markup=REPLY_MARKUP
        )
        return ConversationState.CHOOSING
    question = random.choice(list(quiz_questions_answers.keys()))
    update.message.reply_text(
        question,
        reply_markup=REPLY_MARKUP
    )
    user_id = update.effective_user.id
    redis_db.set(user_id, question)
    return ConversationState.ANSWERING


def handle_solution_attempt(update, context, redis_db, quiz_questions_answers):
    user_answer = update.message.text
    user_id = update.effective_user.id
    asked_question = redis_db.get(user_id).decode('utf-8')
    full_answer = quiz_questions_answers[asked_question]
    short_answer = full_answer.split('.')[0].split('(')[0].strip().lower()
    if user_answer.strip().lower() == short_answer:
        message_text = 'Верно! Для следующего вопроса нажмите "Новый вопрос".'
        update.message.reply_text(message_text, reply_markup=REPLY_MARKUP)
        return ConversationState.CHOOSING
    else:
        message_text = 'Неверно, попробуйте ещё раз.'
        update.message.reply_text(message_text)
        return ConversationState.ANSWERING


def handle_show_answer(update, context, redis_db, quiz_questions_answers):
    if update.message.text == 'Новый вопрос':
        update.message.reply_text(
            'Даже не посмотрите на правильный ответ? )',
            reply_markup=REPLY_MARKUP
        )
        return ConversationState.ANSWERING
    asked_question = redis_db.get(update.message.chat_id).decode('utf-8')
    answer = quiz_questions_answers[asked_question].split('.')[0]
    update.message.reply_text(answer, reply_markup=REPLY_MARKUP)
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
    quiz_questions_answers = load_quizzes_from_directory(quizzes_directory_path)
    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ConversationState.CHOOSING: [
                RegexHandler('^(Новый вопрос|Показать ответ)$', partial(
                    handle_new_question_request,
                    redis_db=redis_db,
                    quiz_questions_answers=quiz_questions_answers)
                )
            ],
            ConversationState.ANSWERING: [
                RegexHandler('^(Новый вопрос|Показать ответ)$', partial(
                    handle_show_answer,
                    redis_db=redis_db,
                    quiz_questions_answers=quiz_questions_answers)
                ),
                MessageHandler(Filters.text, partial(
                    handle_solution_attempt,
                    redis_db=redis_db,
                    quiz_questions_answers=quiz_questions_answers)
                )
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
