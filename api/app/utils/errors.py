# Define custom error messages here

EMAIL_IN_USE = ({'message': 'User with that email already exists'}, 409)
UNAUTHORIZED = (
    {'message': 'Authentication is required to access this resource', 'type': 'UNAUTHORIZED'}, 401)
BAD_CREDENTIALS = (
    {'message': 'Incorrect username or password', 'type': 'BAD_CREDENTIALS'}, 401)
FORBIDDEN = ({'message': 'Access to this resource is forbidden'}, 403)
RESET_PASSWORD_CODE_NOT_VALID = (
    {'message': 'Valid code is required to reset a password'}, 418)
TOO_MANY_REQUESTS = ({'message': 'Too many requests'}, 429)
EVENT_NOT_FOUND = ({'message': 'No event exists with that ID'}, 404)
SECTION_NOT_FOUND = ({'message': 'No section exists with that Event ID'}, 404)
QUESTION_NOT_FOUND = ({'message': 'No question exists with that Event ID'}, 404)
FORM_NOT_FOUND = ({'message': 'No form exists with that Event ID'}, 404)
RESPONSE_NOT_FOUND = (
    {'message': 'No response found for the given event and user'}, 404)
UPDATE_CONFLICT = (
    {'message': 'The requested update conflicts with the existing resource'}, 409)
DB_NOT_AVAILABLE = ({'message': 'Unable to access the database'}, 500)
EMAIL_NOT_VERIFIED = ({'message': 'The email address is not verified'}, 422)
EMAIL_VERIFY_CODE_NOT_VALID = (
    {'message': 'Valid code is required to verify email'}, 419)
USER_NOT_FOUND = ({'message': 'No user exists with that email'}, 404)
RESET_PASSWORD_CODE_EXPIRED = (
    {'message': 'The password reset request has expired'}, 400)
FILE_SIZE_EXCEEDED = ({'message': 'File size exceeded'}, 400)
USER_DELETED = ({'message': 'This account has been deleted'}, 404)
REVIEW_RESPONSE_NOT_FOUND = ({'message': 'No review response found.'}, 404)
ADD_VERIFY_TOKEN_FAILED = (
    {'message': 'Unable to add verification token.'}, 500)
ADD_INVITED_GUEST_FAILED = (
    {'message': 'Unable to add invited guest.'}, 500)
INVITED_GUEST_FOR_EVENT_EXISTS = (
    {'message': 'Invited guest already exists for this event.'}, 409)
VERIFY_EMAIL_INVITED_GUEST = (
    {'message': 'Unable to verify email of invited guest.'}, 500)

VERIFY_EMAIL_OFFER = (
    {'message': 'Unable to verify email of an offer.'}, 500)
MISSING_PASSWORD = (
    {'message': 'Password not provided', 'type': 'MISSING_CREDENTIALS'}, 400)
OFFER_EXPIRED = ({'message': 'This offer has expired'}, 500)
ADD_OFFER_FAILED = (
    {'message': 'Unable to add an offer.'}, 500)
OFFER_NOT_FOUND = (
    {'message': 'No offer found for the given id'}, 404)
REGISTRATION_FORM_NOT_FOUND = (
    {'message': 'No registration form found for the given event and offer'}, 404)
REGISTRATION_SECTION_NOT_FOUND = (
    {'message': 'No registration section found for the given id'}, 404)
REGISTRATION_QUESTION_NOT_FOUND = (
    {'message': 'No registration question found for the given id'}, 404)
ADD_REGISTRATION_FORM_FAILED = (
    {'message': 'Unable to add registration form.'}, 500)
ADD_REGISTRATION_SECTION_FAILED = (
    {'message': 'Unable to add registration section.'}, 500)
ADD_REGISTRATION_QUESTION_FAILED = (
    {'message': 'Unable to add registration question.'}, 500)
ADD_INVITATION_REQUEST_FAILED = (
    {'message': 'Unable to add invitation letter request.'}, 500)
TEMPLATE_NOT_FOUND = (
    {'message': 'No template found for the given parameters'}, 404)
OFFER_NOT_ACCEPTED = (
    {'message': 'Offer has not been accepted'}, 409)
APPLICATIONS_CLOSED = (
    {'message': 'Applications are now closed'}, 403)
NO_ACCOMMODATION_TRAVEL_AWARD = (
    {'message': 'No template found because your offer has neither accommodation nor travel award allocation'}, 404)
