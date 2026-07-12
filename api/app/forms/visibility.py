"""
Form visibility evaluation based on user tags.
"""
from app import db, LOGGER
from app.offer.models import Offer, OfferTag
from app.invitedGuest.models import InvitedGuest, InvitedGuestTag
from app.tags.models import Tag


class VisibilityEvaluator:
    """Evaluates form visibility expressions against user tags"""
    
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
    def evaluate(expression, user_tags):
        """
        Evaluate a visibility expression against user tags.
        
        Args:
            expression: The visibility expression (JSON structure)
            user_tags: Set of tag names (strings) that the user has
        
        Returns:
            bool: True if the user should see the form, False otherwise
        
        Example expressions:
            # Simple tag check
            {"tag": "invited_guest"}
            
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
            
            # Expression with NOT
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
            return VisibilityEvaluator._evaluate_logical(expression, user_tags)
        
        # Handle leaf condition (simple tag check)
        tag = expression.get('tag')
        if tag:
            return tag in user_tags
        
        return False
    
    @staticmethod
    def _evaluate_logical(expression, user_tags):
        """Evaluate logical operators (AND, OR, NOT)"""
        operator = expression.get('operator')
        conditions = expression.get('conditions', [])
        
        if operator == 'AND':
            return all(VisibilityEvaluator.evaluate(cond, user_tags) for cond in conditions)
        
        elif operator == 'OR':
            return any(VisibilityEvaluator.evaluate(cond, user_tags) for cond in conditions)
        
        elif operator == 'NOT':
            if len(conditions) != 1:
                LOGGER.warning(f"NOT operator expects exactly 1 condition, got {len(conditions)}")
                return False
            return not VisibilityEvaluator.evaluate(conditions[0], user_tags)
        
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
