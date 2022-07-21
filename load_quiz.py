from pathlib import Path


def load_quizzes_from_directory(quizzes_directory_path):
    quizzes_directory_path = Path(quizzes_directory_path)
    questions_and_answers = {}
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
                questions_and_answers[question_text] = answer_text
    return questions_and_answers
