def load_quiz_from_file(quiz_file_path):
    with open(quiz_file_path, 'r', encoding='KOI8-R') as quiz_file:
        contents = quiz_file.read()
    questions_and_answers = {}
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
