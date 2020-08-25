from app import LOGGER

def _get_answer_value(answer):
    question = answer.question
    if question.type == 'multi-choice' and question.options is not None:
        value = [o for o in question.options if o['value'] == answer.value]
        if not value:
            return answer.value
        return value[0]['label']
    
    if question.type == 'file' and answer.value:
        return 'Uploaded File'

    return answer.value

def build_response_email_greeting(title, firstname, lastname):
    return ('Dear {title} {firstname} {lastname},'.format(title=title, firstname=firstname, lastname=lastname))

def build_response_email_body(answers, language):
    #stringifying the dictionary summary, with linebreaks between question/answer pairs
    stringified_summary = None
    for answer in answers:
        question_translation = answer.question.get_translation(language)
        if question_translation is None:
            LOGGER.error('Missing {} translation for question {}.'.format(language, answer.question.id))
            question_translation = answer.question.get_translation('en')
        question_headline = question_translation.headline

        answer_value = _get_answer_value(answer)
        if(stringified_summary is None):
            stringified_summary = '{question}:\n{answer}'.format(question=question_headline, answer=answer_value)
        else:
            stringified_summary = '{current_summary}\n\n{question}:\n{answer}'.format(current_summary=stringified_summary, question=question_headline, answer=answer_value)

    return stringified_summary
