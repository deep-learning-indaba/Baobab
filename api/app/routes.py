from app import rest_api

from users import api as users_api


rest_api.add_resource(users_api.UserAPI, '/api/v1/user')
rest_api.add_resource(users_api.AuthenticationAPI, '/api/v1/authenticate')
rest_api.add_resource(users_api.PasswordResetRequestAPI, '/api/v1/password-reset/request')
rest_api.add_resource(users_api.PasswordResetConfirmAPI, '/api/v1/password-reset/confirm')
rest_api.add_resource(users_api.AdminOnlyAPI, '/api/v1/admin')
