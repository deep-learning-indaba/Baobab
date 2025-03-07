# -*- coding: utf-8 -*-

from app import LOGGER
import json

def _get_answer_value(answer, question, question_translation):
    if answer is None:
        if question_translation.language == 'fr':  # TODO: Add proper language support for back-end text
            return 'Aucune réponse fournie'
        else:
            return 'No answer provided'

    if question.type == 'multi-choice' and question_translation.options is not None:
        value = [o for o in question_translation.options if o['value'] == answer.value]
        if not value:
            return answer.value
        return value[0]['label']
    
    if question.type == 'file' and answer.value:
        if question_translation.language == 'fr':
            return 'Fichier téléchargé'
        else:
            return 'Uploaded File'

    if question.type == 'multi-file' and answer.value:
        file_info = json.loads(answer.value)
        return "\n".join([f['name'] for f in file_info])

    if question.type == 'information':
        return ""

    return answer.value

def _find_answer(question, answers):
    if question == None:
        return None

    answer = [a for a in answers if a.question_id == question.id]
    if answer:
        return answer[0]
    else:
        return None

def _find_question(question_id, questions):
    question = [q for q in questions if q.id == question_id]
    if question:
        return question[0]
    else:
        return None

def build_response_email_body(answers, language, application_form):
    #stringifying the dictionary summary, with linebreaks between question/answer pairs
    stringified_summary = ""

    allQuestions = [q for section in application_form.sections for q in section.questions]

    for section in application_form.sections:
        if not section.questions:
            continue
        section_translation = section.get_translation(language)
        if section_translation is None:
            LOGGER.error('Missing {} translation for section {}.'.format(language, section.id))
            section_translation = section.get_translation('en')
        stringified_summary += section_translation.name + '\n' + '-' * 20 + '\n\n'
        for question in section.questions:
            question_translation = question.get_translation(language)
            if question_translation is None:
                LOGGER.error('Missing {} translation for question {}.'.format(language, question.id))
                question_translation = question.get_translation('en')

            if question.depends_on_question_id and question_translation.show_for_values:
                dependency_question = _find_question(question.depends_on_question_id, allQuestions)
                dependency_answer = _find_answer(dependency_question, answers)
                if dependency_answer and dependency_answer not in question_translation.show_for_values:
                    continue

            answer = _find_answer(question, answers)

            if answer:
                answer_value = _get_answer_value(answer, answer.question, question_translation)
                stringified_summary += '{question}\n{answer}\n\n'.format(question=question_translation.headline, answer=answer_value)

    return stringified_summary

def answer_by_question_key(key, application_form, answers):
    """
    Recherche la réponse associée à une question donnée par sa clé.
    
    :param key: Clé de la question recherchée.
    :param application_form: Formulaire d'application contenant les sections et questions.
    :param answers: Dictionnaire des réponses fournies.
    :return: Valeur de la réponse si trouvée, sinon None.
    """
    all_questions = [q for section in application_form.sections for q in section.questions]
    
    question = next((q for q in all_questions if q.key == key), None)
    
    if question:
        answer = next((a for a in answers if a.question_id == question.id), None)
        if answer:
            return answer.value
    
    return None


def build_response_html_app_info(response, language):
    """
    Stringifying the application information, for output in a html file, with the response_id and applicant name contact info as
     paragraphs (<p>)
    """
    
    stringified_app_info = f"<p><b> Response ID:</b> {response.id}</p> <p><b>Full name:</b> {response.user.firstname} {response.user.lastname}</p>"

    return "<title>Application Responses</title>" + stringified_app_info


def build_response_html_answers(answers, language, application_form):
    """
    Stringifying the dictionary answers, for output in a html file, with sections as headers(<h1>), 
    questions as second headings (<h2>) and answers as paragraphs (<p>)
    """

    stringified_answers = ""

    for section in application_form.sections:
        if not section.questions:
            continue
        section_translation = section.get_translation(language)
        if section_translation is None:
            LOGGER.error('Missing {} translation for section {}.'.format(language, section.id))
            section_translation = section.get_translation('en')
        stringified_answers += '<h1>' + section_translation.name + '</h1>' 

        for question in section.questions:
            question_translation = question.get_translation(language)
            if question_translation is None:
                LOGGER.error('Missing {} translation for question {}.'.format(language, question.id))
                question_translation = question.get_translation('en')

            answer = _find_answer(question, answers)
            if answer:
                answer_value = _get_answer_value(answer, answer.question, question_translation)
                stringified_answers += f"<h2> {question_translation.headline} </h2> <p>{answer_value}</p>"


    return stringified_answers


def build_review_email_body(review_responses, language, review_form):
    """
    Build a string summary of all reviews for a particular response,
    similar to build_response_email_body, but without dependencies.
    """

    summary_str = ""
    for idx, review_response in enumerate(review_responses, start=1):
        summary_str += f"Reviewer {idx}\n\n"

        for section in review_form.review_sections:
            if not section.review_questions:
                continue

            section_translation = section.get_translation(language)
            if not section_translation:
                section_translation = section.get_translation('en')
            section_title = section_translation.headline
            summary_str += section_title + "\n" + ("-" * 20) + "\n\n"

            for question in section.review_questions:
                question_translation = question.get_translation(language)
                if not question_translation:
                    question_translation = question.get_translation('en')

                found_score = next(
                    (score for score in review_response["scores"]
                     if score["review_question_id"] == question.id),
                    None
                )
                if found_score:
                    answer_value = found_score.get("value", "")
                    summary_str += (
                        f"{question_translation.headline}\n"
                        f"{answer_value}\n\n"
                    )

        summary_str += "\n"

    return summary_str

def _find_question(question_id, all_questions):
    for question in all_questions:
        if question.id == question_id:
            return question
    return None

def _find_answer(question, scores):
    if not question:
        return None
    found = next(
        (score for score in scores if score["review_question_id"] == question.id),
        None
    )
    if found:
        # If your code expects a raw "value" or something else, adapt here:
        return found.get("value")
    return None
