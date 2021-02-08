import uuid

import flask_restful as restful
from flask_restful import reqparse
from flask import send_file
from config import FILE_SIZE_LIMIT
from app.utils.errors import FILE_SIZE_EXCEEDED
from app.files.mixins import FileUploadMixin
from app.utils.auth import auth_required

import tempfile

from app import LOGGER
from app.utils import storage


class FileUploadAPI(FileUploadMixin, restful.Resource):
    
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('filename', type=str, required=True)
        req_parser.add_argument('rename', type=str, required=False)
        args = req_parser.parse_args()

        bucket = storage.get_storage_bucket()

        blob = bucket.blob(args['filename'])
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            renamed = args['rename'] or args['filename']
            return send_file(
                temp.name, 
                as_attachment=True, 
                attachment_filename=args['rename'] or args['filename'])


    def post(self):
        args = self.req_parser.parse_args()

        bucket = storage.get_storage_bucket()
        
        unique_name = str(uuid.uuid4().hex)
        blob = bucket.blob(unique_name)

        file = args['file']
        bytes_file = file.read()
        content_type = file.content_type
        file_size = len(bytes_file) 

        if file_size > FILE_SIZE_LIMIT:
            LOGGER.debug('File size of {} exceeds limit of {}'.format(file_size, FILE_SIZE_EXCEEDED))
            return FILE_SIZE_EXCEEDED

        blob.upload_from_string(bytes_file, content_type=content_type)

        return {
            'file_id': unique_name,
        }, 201
