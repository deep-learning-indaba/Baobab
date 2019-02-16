from app import rest_api
from applicationModel import api as form_api
from users import api as users_api
from responses import api as responses_api
from files import api as files_api


rest_api.add_resource(users_api.UserAPI, '/api/v1/user')
rest_api.add_resource(users_api.AuthenticationAPI, '/api/v1/authenticate')
rest_api.add_resource(users_api.PasswordResetRequestAPI, '/api/v1/password-reset/request')
rest_api.add_resource(users_api.PasswordResetConfirmAPI, '/api/v1/password-reset/confirm')
rest_api.add_resource(users_api.AdminOnlyAPI, '/api/v1/admin')
rest_api.add_resource(form_api.ApplicationFormAPI, '/api/v1/application-form')
rest_api.add_resource(responses_api.ResponseAPI, '/api/v1/response')
rest_api.add_resource(files_api.FileUploadAPI, '/api/v1/file')
