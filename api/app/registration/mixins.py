from flask_restful import reqparse

class RegistrationMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int,required=True)
    req_parser.add_argument('event_id',type=int, required=True)
    req_parser.add_argument('offer_date',type=str, required=True)
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('accepted', type=bool, required=False)
    req_parser.add_argument('rejected', type=bool, required=False)
    req_parser.add_argument('rejected_reason', type=str, required=False)
