"""
Form visibility evaluation based on user tags.
"""
from app import db, LOGGER
from app.offer.models import Offer, OfferTag
from app.invitedGuest.models import InvitedGuest, InvitedGuestTag
from app.tags.models import Tag
from app.forms.models import DependencyOperator

#: Operators the `key`/`operator` answer-comparison leaf accepts. A subset of
#: DependencyOperator (form question dependencies): numeric/text-pattern
#: operators aren't offered because the values being compared are already
#: humanised strings (option labels, joined multi-values), not raw typed input.
ANSWER_COMPARISON_OPERATORS = {
    DependencyOperator.EQUALS.value, DependencyOperator.NOT_EQUALS.value,
    DependencyOperator.IN.value, DependencyOperator.NOT_IN.value,
    DependencyOperator.IS_EMPTY.value, DependencyOperator.IS_NOT_EMPTY.value,
}


class VisibilityEvaluator:
    """Evaluates form visibility expressions against user tags.

    Also used, via the optional `context` argument, for document eligibility,
    variant-selection and derived-placeholder rules (app/documents/eligibility.py,
    app/documents/derived_placeholders.py) - one expression language for all
    four, so admins learn a single rule builder.
    """

    @staticmethod
    def get_user_tag_ids_for_event(user_id, event_id):
        """Like get_user_tags_for_event, but tag ids rather than translated names.

        Expressions built by an admin UI should reference tags by id: matching on
        the English translated name (as the `tag` leaf below does) means renaming
        a tag silently breaks every expression that names it.
        """
        tag_ids = set()

        offer = db.session.query(Offer).filter_by(user_id=user_id, event_id=event_id).first()
        if offer:
            for offer_tag in offer.offer_tags:
                if offer_tag.tag and offer_tag.tag.active:
                    tag_ids.add(offer_tag.tag_id)

        invited_guest = db.session.query(InvitedGuest).filter_by(
            user_id=user_id, event_id=event_id).first()
        if invited_guest:
            for guest_tag in invited_guest.invited_guest_tags:
                if guest_tag.tag and guest_tag.tag.active:
                    tag_ids.add(guest_tag.tag_id)

        return tag_ids

    @staticmethod
    def get_user_tags_for_event(user_id, event_id):
        """
        Get all tags for a user in an event context.
        
        Returns a set of tag names (strings) that the user has, including:
        - Tags from Offer (if user has an offer for the event)
        - Tags from InvitedGuest (if user is an invited guest)
        - Automatic tags: 'invited_guest', 'selected_attendee'
        
        Args:
            user_id: The user's ID
            event_id: The event's ID
            
        Returns:
            set: Set of tag names (strings) that the user has
        """
        user_tags = set()
        
        # Check if user has an offer (selected attendee)
        offer = db.session.query(Offer).filter_by(
            user_id=user_id,
            event_id=event_id
        ).first()
        
        if offer:
            # Add automatic tag
            user_tags.add('selected_attendee')
            
            # Add tags from offer
            for offer_tag in offer.offer_tags:
                if offer_tag.tag and offer_tag.tag.active:
                    tag_name = offer_tag.tag.stringify_tag_name('en')
                    user_tags.add(tag_name)
        
        # Check if user is an invited guest
        invited_guest = db.session.query(InvitedGuest).filter_by(
            user_id=user_id,
            event_id=event_id
        ).first()
        
        if invited_guest:
            # Add automatic tag
            user_tags.add('invited_guest')
            
            # Add tags from invited guest
            for guest_tag in invited_guest.invited_guest_tags:
                if guest_tag.tag and guest_tag.tag.active:
                    tag_name = guest_tag.tag.stringify_tag_name('en')
                    user_tags.add(tag_name)
        
        return user_tags
    
    @staticmethod
    def evaluate(expression, user_tags, context=None):
        """
        Evaluate a visibility expression against user tags.

        Args:
            expression: The visibility expression (JSON structure)
            user_tags: Set of tag names (strings) that the user has
            context: Optional EligibilityContext supplying tag ids, the
                `attended` / `form_submitted` leaves, and answers for the
                `key`/`operator` leaf (app/documents/eligibility.py). Forms
                visibility never passes this, so those leaves evaluate to
                False for form dependencies - unchanged behaviour for existing
                callers.

        Returns:
            bool: True if the user should see the form, False otherwise

        Example expressions:
            # Simple tag check
            {"tag": "invited_guest"}

            # Tag by id - preferred for anything built by an admin UI, since it
            # survives the tag being renamed
            {"tag_id": 12}

            # Complex expression with AND
            {
                "operator": "AND",
                "conditions": [
                    {"tag": "selected_attendee"},
                    {"tag": "workshop_participant"}
                ]
            }

            # Expression with OR
            {
                "operator": "OR",
                "conditions": [
                    {"tag": "invited_guest"},
                    {"tag": "selected_attendee"}
                ]
            }

            # Expression with NOT - exactly one condition
            {
                "operator": "NOT",
                "conditions": [
                    {"tag": "blacklisted"}
                ]
            }
        """
        if not expression:
            return True

        operator = expression.get('operator')

        # Handle logical operators (AND, OR, NOT)
        if operator in ['AND', 'OR', 'NOT']:
            return VisibilityEvaluator._evaluate_logical(expression, user_tags, context)

        if 'tag' in expression:
            return expression.get('tag') in user_tags

        if 'tag_id' in expression:
            return context is not None and expression.get('tag_id') in context.tag_ids

        if 'attended' in expression:
            return context is not None and context.attended == bool(expression.get('attended'))

        if 'form_submitted' in expression:
            return (context is not None
                    and expression.get('form_submitted') in context.submitted_form_ids)

        if 'key' in expression and 'operator' in expression:
            return VisibilityEvaluator._evaluate_answer(expression, context)

        return False

    @staticmethod
    def _evaluate_answer(expression, context):
        """`{"key": "bringing_poster", "operator": "EQUALS", "value": "yes"}`

        True when the resolved placeholder value for `key` (the same
        precedence chain a document placeholder is resolved through - linked
        forms, user data, profile, event, system) compares as requested.
        Requires a context that implements `get_answer_value(key)`; plain form
        visibility never supplies one, so this leaf is always False there.
        """
        if context is None or not hasattr(context, 'get_answer_value'):
            return False

        operator = expression.get('operator')
        if operator not in ANSWER_COMPARISON_OPERATORS:
            LOGGER.warning('Unknown answer-comparison operator: %s', operator)
            return False

        raw_value = context.get_answer_value(expression.get('key'))
        is_blank = raw_value is None or raw_value == ''

        if operator == DependencyOperator.IS_EMPTY.value:
            return is_blank
        if operator == DependencyOperator.IS_NOT_EMPTY.value:
            return not is_blank

        # Blank compares as an empty string rather than short-circuiting, so
        # EQUALS/NOT_EQUALS/IN/NOT_IN behave the same whether the value came
        # back None or "" - both mean "nothing here".
        value = '' if is_blank else str(raw_value).strip().lower()
        if operator == DependencyOperator.EQUALS.value:
            return value == str(expression.get('value', '')).strip().lower()
        if operator == DependencyOperator.NOT_EQUALS.value:
            return value != str(expression.get('value', '')).strip().lower()
        if operator == DependencyOperator.IN.value:
            return value in {str(v).strip().lower() for v in expression.get('values', [])}
        if operator == DependencyOperator.NOT_IN.value:
            return value not in {str(v).strip().lower() for v in expression.get('values', [])}
        return False

    @staticmethod
    def _evaluate_logical(expression, user_tags, context=None):
        """Evaluate logical operators (AND, OR, NOT)"""
        operator = expression.get('operator')
        conditions = expression.get('conditions', [])

        if operator == 'AND':
            return all(VisibilityEvaluator.evaluate(cond, user_tags, context) for cond in conditions)

        elif operator == 'OR':
            return any(VisibilityEvaluator.evaluate(cond, user_tags, context) for cond in conditions)

        elif operator == 'NOT':
            if len(conditions) != 1:
                LOGGER.warning(f"NOT operator expects exactly 1 condition, got {len(conditions)}")
                return False
            return not VisibilityEvaluator.evaluate(conditions[0], user_tags, context)

        return False
    
    @staticmethod
    def check_form_visibility(form, user_id, event_id):
        """
        Check if a user can see a form based on its visibility expression.
        
        Args:
            form: Form object
            user_id: User's ID
            event_id: Event's ID
            
        Returns:
            bool: True if user can see the form, False otherwise
        """
        if not form.visibility_expression:
            return True
        
        user_tags = VisibilityEvaluator.get_user_tags_for_event(user_id, event_id)
        return VisibilityEvaluator.evaluate(form.visibility_expression, user_tags)
