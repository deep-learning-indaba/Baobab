#Define and create string builders here

RESPONSE_BODY = """Thank you for applying to attend {event_description}. Your application is being reviewed by our committee and we will get back to you as soon as possible. Included below is a copy of your responses.


{summary}


Kind Regards,
The {event_name} Organising Committee
"""

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

def build_response_email_body(event_name, event_description, answers):
    #stringifying the dictionary summary, with linebreaks between question/answer pairs
    stringified_summary = None
    for answer in answers:
        question_headline = answer.question.headline
        answer_value = _get_answer_value(answer)
        if(stringified_summary is None):
            stringified_summary = '{question}:\n{answer}'.format(question=question_headline, answer=answer_value)
        else:
            stringified_summary = '{current_summary}\n\n{question}:\n{answer}'.format(current_summary=stringified_summary, question=question_headline, answer=answer_value)

    return (RESPONSE_BODY.format(event_description=event_description, event_name=event_name, summary=stringified_summary))
