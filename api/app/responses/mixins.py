from flask_restful import reqparse


class ResponseMixin(object):
    get_req_parser = reqparse.RequestParser()
    get_req_parser.add_argument(
        "event_id",
        type=int,
        required=True,
        help="Invalid event_id requested. Event_id's should be of type int.",
    )

    post_req_parser = reqparse.RequestParser()
    post_req_parser.add_argument("is_submitted", type=bool, required=True)
    post_req_parser.add_argument("application_form_id", type=int, required=True)
    post_req_parser.add_argument("answers", type=list, required=True, location="json")
    post_req_parser.add_argument("language", type=str, required=True)

    put_req_parser = reqparse.RequestParser()
    put_req_parser.add_argument("id", type=int, required=True)
    put_req_parser.add_argument("is_submitted", type=bool, required=True)
    put_req_parser.add_argument("application_form_id", type=int, required=True)
    put_req_parser.add_argument("answers", type=list, required=True, location="json")
    put_req_parser.add_argument("language", type=str, required=True)

    del_req_parser = reqparse.RequestParser()
    del_req_parser.add_argument("id", type=int, required=True)


class ResponseTagMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument("event_id", type=int, required=True)
    req_parser.add_argument("tag_id", type=int, required=True)
    req_parser.add_argument("response_id", type=int, required=True)
