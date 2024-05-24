from flask_restful import reqparse


class OfferMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('id', type=int, required=False)
    req_parser.add_argument('event_id', type=int, required=False)
    req_parser.add_argument('offer_id', type=int, required=False)
    req_parser.add_argument('user_id', type=int, required=False)
    req_parser.add_argument('offer_date', type=str, required=False)
    req_parser.add_argument('expiry_date', type=str, required=False)
    req_parser.add_argument('payment_required', type=bool, required=False)
    req_parser.add_argument('grant_tags', type=list, location='json', required=False, default=[])
    req_parser.add_argument('rejected_reason', type=str, required=False)
    req_parser.add_argument('candidate_response', type=bool, required=False)
    req_parser.add_argument('responded_at', type=str, required=False)
    req_parser.add_argument('email_template', type=str, required=False)
    req_parser.add_argument('event_fee_id', type=int, required=False)

class OfferTagMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('tag_id', type=int, required=True)
    req_parser.add_argument('offer_id', type=int, required=True)
    req_parser.add_argument('accepted', type=bool, required=False)