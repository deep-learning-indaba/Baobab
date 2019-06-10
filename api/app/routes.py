from app import rest_api
from applicationModel import api as form_api
from users import api as users_api
from responses import api as responses_api
from content import api as content_api
from files import api as files_api
from events import api as events_api
from reviews import api as reviews_api
from invitedGuest import api as invitedGuest_api
from registration import api as registration_api
from registrationResponse import response as registration_response


rest_api.add_resource(users_api.UserAPI, '/api/v1/user')
rest_api.add_resource(users_api.UserCommentAPI, '/api/v1/user-comment')
rest_api.add_resource(users_api.AuthenticationAPI, '/api/v1/authenticate')
rest_api.add_resource(users_api.PasswordResetRequestAPI,
                      '/api/v1/password-reset/request')
rest_api.add_resource(users_api.PasswordResetConfirmAPI,
                      '/api/v1/password-reset/confirm')
rest_api.add_resource(users_api.AdminOnlyAPI, '/api/v1/admin')
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
rest_api.add_resource(events_api.EventStatsAPI,
                      '/api/v1/eventstats'),
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
rest_api.add_resource(registration_api.RegistrationFormAPI,
                      '/api/v1/registration-form')
rest_api.add_resource(registration_api.RegistrationSectionAPI,
                      '/api/v1/registration-section')
rest_api.add_resource(registration_api.RegistrationQuestionAPI,
                      '/api/v1/registration-question')
rest_api.add_resource(registration_response.RegistrationApi,
                      '/api/v1/registration-response')
