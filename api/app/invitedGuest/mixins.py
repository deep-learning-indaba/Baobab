from flask_restful import reqparse
class InvitedGuestListMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('language', type=str, required=True)

class InvitedGuestTagMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('event_id', type=int, required=True)
    req_parser.add_argument('tag_id', type=int, required=True)
    req_parser.add_argument('invited_guest_id', type=int, required=True)
    req_parser.add_argument('language', type=str, required=True)

