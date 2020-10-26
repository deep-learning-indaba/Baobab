from app import rest_api
from applicationModel import api as form_api
from users import api as users_api
from responses import api as responses_api
from content import api as content_api
from files import api as files_api
from events import api as events_api
from reviews import api as reviews_api
from invitedGuest import api as invitedGuest_api
from references import api as reference_api
from registration import api as registration_api
from registrationResponse import api as registration_response
from guestRegistrations import api as guest_registration
from invitationletter import api as invitation_letter_api
from attendance import api as attendance_api
from organisation import api as organisation_api
from integration_tests import api as integration_tests_api
from outcome import api as outcome_api

rest_api.add_resource(users_api.UserAPI, '/api/v1/user')
rest_api.add_resource(users_api.UserCommentAPI, '/api/v1/user-comment')
rest_api.add_resource(users_api.AuthenticationAPI, '/api/v1/authenticate')
rest_api.add_resource(users_api.PasswordResetRequestAPI,
                      '/api/v1/password-reset/request')
rest_api.add_resource(users_api.PasswordResetConfirmAPI,
                      '/api/v1/password-reset/confirm')
rest_api.add_resource(users_api.AdminOnlyAPI, '/api/v1/admin')
rest_api.add_resource(users_api.EmailerAPI,
                      '/api/v1/admin/emailer')
rest_api.add_resource(form_api.ApplicationFormAPI, '/api/v1/application-form')
rest_api.add_resource(responses_api.ResponseAPI, '/api/v1/response')
rest_api.add_resource(content_api.CountryContentAPI,
                      '/api/v1/content/countries')
rest_api.add_resource(files_api.FileUploadAPI, '/api/v1/file')
rest_api.add_resource(content_api.CategoryContentAPI,
                      '/api/v1/content/categories')
rest_api.add_resource(content_api.EthnicityContentAPI,
                      '/api/v1/content/ethnicity')
rest_api.add_resource(content_api.TitleContentAPI,
                      '/api/v1/content/title'),
rest_api.add_resource(content_api.DisabilityContentAPI,
                      '/api/v1/content/disability'),
rest_api.add_resource(content_api.GenderContentAPI,
                      '/api/v1/content/gender'),
rest_api.add_resource(events_api.EventsAPI,
                      '/api/v1/events'),
rest_api.add_resource(events_api.EventAPI,
                      '/api/v1/event'),
rest_api.add_resource(events_api.EventStatsAPI,
                      '/api/v1/eventstats'),
rest_api.add_resource(events_api.EventsByKeyAPI,
                      '/api/v1/event-by-key'),
rest_api.add_resource(users_api.VerifyEmailAPI,
                      '/api/v1/verify-email'),
rest_api.add_resource(users_api.ResendVerificationEmailAPI,
                      '/api/v1/resend-verification-email'),
rest_api.add_resource(reviews_api.ReviewAPI, '/api/v1/review')
rest_api.add_resource(reviews_api.ReviewResponseAPI, '/api/v1/reviewresponse')
rest_api.add_resource(reviews_api.ReviewAssignmentAPI,
                      '/api/v1/reviewassignment')
rest_api.add_resource(reviews_api.ReviewSummaryAPI,
                      '/api/v1/reviewassignment/summary')
rest_api.add_resource(events_api.NotSubmittedReminderAPI,
                      '/api/v1/reminder-unsubmitted')
rest_api.add_resource(events_api.NotStartedReminderAPI,
                      '/api/v1/reminder-not-started')
rest_api.add_resource(reviews_api.ReviewHistoryAPI, '/api/v1/reviewhistory')
rest_api.add_resource(users_api.UserProfileList, '/api/v1/userprofilelist')
rest_api.add_resource(users_api.UserProfile, '/api/v1/userprofile')
rest_api.add_resource(invitedGuest_api.InvitedGuestAPI, '/api/v1/invitedGuest')
rest_api.add_resource(invitedGuest_api.CreateUser,
                      '/api/v1/invitedGuest/create')
rest_api.add_resource(invitedGuest_api.InvitedGuestList,
                      '/api/v1/invitedGuestList')
rest_api.add_resource(invitedGuest_api.CheckIfInvitedGuest,
                      '/api/v1/checkIfInvitedGuest')
rest_api.add_resource(reference_api.ReferenceRequestListAPI,
                      '/api/v1/reference-request/list')
rest_api.add_resource(reference_api.ReferenceRequestDetailAPI,
                      '/api/v1/reference-request/detail')
rest_api.add_resource(reference_api.ReferenceRequestAPI,
                      '/api/v1/reference-request')
rest_api.add_resource(reference_api.ReferenceAPI,
                      '/api/v1/reference')
rest_api.add_resource(registration_api.OfferAPI, '/api/v1/offer')
rest_api.add_resource(registration_api.RegistrationFormAPI,
                      '/api/v1/registration-form')
rest_api.add_resource(registration_api.RegistrationSectionAPI,
                      '/api/v1/registration-section')
rest_api.add_resource(registration_api.RegistrationQuestionAPI,
                      '/api/v1/registration-question')
rest_api.add_resource(registration_response.RegistrationApi,
                      '/api/v1/registration-response')
rest_api.add_resource(guest_registration.GuestRegistrationApi,
                      '/api/v1/guest-registration')
rest_api.add_resource(guest_registration.GuestRegistrationFormAPI,
                      '/api/v1/guest-registration-form')
rest_api.add_resource(registration_response.RegistrationUnconfirmedAPI,
                      '/api/v1/registration/unconfirmed')
rest_api.add_resource(registration_response.RegistrationConfirmedAPI,
                      '/api/v1/registration/confirmed')
rest_api.add_resource(registration_response.RegistrationConfirmAPI,
                      '/api/v1/registration/confirm')
rest_api.add_resource(invitation_letter_api.InvitationLetterAPI,
                      '/api/v1/invitation-letter')
rest_api.add_resource(attendance_api.AttendanceAPI, '/api/v1/attendance')
rest_api.add_resource(organisation_api.OrganisationApi, '/api/v1/organisation')
rest_api.add_resource(users_api.PrivacyPolicyAPI, '/api/v1/privacypolicy')
rest_api.add_resource(integration_tests_api.CreateIntegrationUser, '/api/v1/integration-tests/createUser')
rest_api.add_resource(integration_tests_api.DeleteIntegrationUser, '/api/v1/integration-tests/deleteUser')
rest_api.add_resource(outcome_api.OutcomeAPI, '/api/v1/outcome')
rest_api.add_resource(outcome_api.OutcomeListAPI, '/api/v1/outcome-list')
rest_api.add_resource(users_api.EventAttendeeAPI, '/api/v1/validate-user-event-attendee')
rest_api.add_resource(form_api.QuestionListApi, '/api/v1/questions')
