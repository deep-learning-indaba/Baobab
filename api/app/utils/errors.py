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
SECTION_NOT_FOUND = ({'message': 'No event exists with that ID'}, 409)
QUESTION_NOT_FOUND = ({'message': 'No event exists with that ID'}, 409)
FORM_NOT_FOUND = ({'message': 'No event exists with that ID'}, 404)
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
