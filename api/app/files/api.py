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
        req_parser.add_argument('bucket', type=str, required=False)
        req_parser.add_argument('disposition', type=str, required=False, choices=('inline', 'attachment'))
        args = req_parser.parse_args()

        LOGGER.info("Downloading file: {}, from bucket".format(args['filename'], args['bucket']))
        bucket = storage.get_storage_bucket(args['bucket'])

        # Fetch the stored content-type both to decide disposition when the
        # caller didn't say (auto: images inline, everything else attachment)
        # and to serve it as the response mimetype - the blob name itself has
        # no extension, so Flask can't guess it from the filename, regardless
        # of disposition. Use a throwaway Blob for this: reload() populates
        # media_link from whatever the storage backend reports, and
        # download_to_filename() then prefers that over the configured
        # endpoint, which breaks downloads against the local storage emulator.
        meta_blob = bucket.blob(args['filename'])
        meta_blob.reload()
        content_type = meta_blob.content_type

        disposition = args['disposition']
        if not disposition:
            disposition = 'inline' if (content_type or '').startswith('image/') else 'attachment'

        blob = bucket.blob(args['filename'])
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(
                temp.name,
                mimetype=content_type,
                as_attachment=(disposition == 'attachment'),
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
