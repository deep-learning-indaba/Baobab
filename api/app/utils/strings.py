# -*- coding: utf-8 -*-

import json

from app import LOGGER


def _get_answer_value(answer, question, question_translation):
    if answer is None:
        if (
            question_translation.language == "fr"
        ):  # TODO: Add proper language support for back-end text
            return "Aucune réponse fournie"
        else:
            return "No answer provided"

    if question.type == "multi-choice" and question_translation.options is not None:
        value = [o for o in question_translation.options if o["value"] == answer.value]
        if not value:
            return answer.value
        return value[0]["label"]

    if question.type == "file" and answer.value:
        if question_translation.language == "fr":
            return "Fichier téléchargé"
        else:
            return "Uploaded File"

    if question.type == "multi-file" and answer.value:
        file_info = json.loads(answer.value)
        return "\n".join([f["name"] for f in file_info])

    if question.type == "information":
        return ""

    return answer.value


def _find_answer(question, answers):
    answer = [a for a in answers if a.question_id == question.id]
    if answer:
        return answer[0]
    else:
        return None


def build_response_email_body(answers, language, application_form):
    # stringifying the dictionary summary, with linebreaks between question/answer pairs
    stringified_summary = ""

    for section in application_form.sections:
        if not section.questions:
            continue
        section_translation = section.get_translation(language)
        if section_translation is None:
            LOGGER.error(
                "Missing {} translation for section {}.".format(language, section.id)
            )
            section_translation = section.get_translation("en")
        stringified_summary += section_translation.name + "\n" + "-" * 20 + "\n\n"
        for question in section.questions:
            question_translation = question.get_translation(language)
            if question_translation is None:
                LOGGER.error(
                    "Missing {} translation for question {}.".format(
                        language, question.id
                    )
                )
                question_translation = question.get_translation("en")

            answer = _find_answer(question, answers)
            if answer:
                answer_value = _get_answer_value(
                    answer, answer.question, question_translation
                )
                stringified_summary += "{question}\n{answer}\n\n".format(
                    question=question_translation.headline, answer=answer_value
                )

    return stringified_summary


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
            LOGGER.error(
                "Missing {} translation for section {}.".format(language, section.id)
            )
            section_translation = section.get_translation("en")
        stringified_answers += "<h1>" + section_translation.name + "</h1>"

        for question in section.questions:
            question_translation = question.get_translation(language)
            if question_translation is None:
                LOGGER.error(
                    "Missing {} translation for question {}.".format(
                        language, question.id
                    )
                )
                question_translation = question.get_translation("en")

            answer = _find_answer(question, answers)
            if answer:
                answer_value = _get_answer_value(
                    answer, answer.question, question_translation
                )
                stringified_answers += (
                    f"<h2> {question_translation.headline} </h2> <p>{answer_value}</p>"
                )

    return stringified_answers
