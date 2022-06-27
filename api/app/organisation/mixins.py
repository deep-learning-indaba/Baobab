from flask_restful import reqparse

class StripeSettingsMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('iso_currency_code', type=str, required=True)
    req_parser.add_argument('publishable_key', type=str, required=True)
    req_parser.add_argument('secret_key', type=str, required=True)
    req_parser.add_argument('webhook_secret_key', type=str, required=True)