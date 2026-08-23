"""Picks which DocumentTemplateVariant a given recipient gets.

An attendee asks for "an invitation letter"; which of several underlying
Google files they get is decided here, invisibly to them, from their tags and
requested language. See design section 7.3.
"""
from app.documents.eligibility import evaluate_expression


class NoMatchingVariant(Exception):
    pass


def select_variant(document_template, context, language='en'):
    """The variant this recipient should get, or raises NoMatchingVariant.

    Language preference: variants pinned to the requested language are tried
    first; if none exist, language-agnostic variants (language=None) are
    tried instead. A variant pinned to a *different* language is never picked
    - that would silently hand a French speaker an English letter instead of
    falling through to a language-agnostic one.

    Within whichever language group applies, variants are tried in descending
    priority, first match wins. A variant with no selection_expression matches
    everyone, so giving it the lowest priority makes it the catch-all.
    """
    candidates = [v for v in document_template.active_variants()]
    if not candidates:
        raise NoMatchingVariant('This document template has no active variants.')

    language_matches = [v for v in candidates if v.language == language]
    pool = language_matches if language_matches else [v for v in candidates if v.language is None]

    for variant in sorted(pool, key=lambda v: (-v.priority, v.id)):
        if evaluate_expression(variant.selection_expression, context):
            return variant

    raise NoMatchingVariant(
        'No variant of this document matches this person\'s tags. '
        'Add a catch-all variant (no selection rule) to avoid this.'
    )


def is_eligible(document_template, context):
    """Whether `context`'s tags/attendance satisfy the template's eligibility rule.

    A null eligibility_expression matches everyone, mirroring form
    visibility_expression's "no rule means unrestricted" convention.
    """
    return evaluate_expression(document_template.eligibility_expression, context)
