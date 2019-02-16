from flask_restful import reqparse
from werkzeug.datastructures import FileStorage

class FileUploadMixin(object):
    req_parser = reqparse.RequestParser()
    req_parser.add_argument('file', location='files', type=FileStorage, required=True)