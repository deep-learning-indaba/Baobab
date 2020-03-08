import uuid

import flask_restful as restful
from flask_restful import reqparse
from flask import send_file
from config import GCP_CREDENTIALS_DICT, GCP_PROJECT_NAME, GCP_BUCKET_NAME, FILE_SIZE_LIMIT
from app.utils.errors import FILE_SIZE_EXCEEDED
from app.files.mixins import FileUploadMixin
from app.files.models import File
from app.files.repository import FileRepository as file_repository
from app.utils.auth import auth_required

from google.cloud import storage
from google.oauth2 import service_account

import tempfile

from app import db, LOGGER

def _get_storage_bucket():
    if GCP_CREDENTIALS_DICT['private_key'] == 'dummy':
        LOGGER.debug('Setting dummy storage client')
        storage_client = storage.Client(project=GCP_PROJECT_NAME)
    else:
        LOGGER.debug('Setting GCP storage client')
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )
        storage_client = storage.Client(credentials=credentials, project=GCP_PROJECT_NAME)

    return storage_client.get_bucket(GCP_BUCKET_NAME)


class FileUploadAPI(FileUploadMixin, restful.Resource):
    
    def get(self):
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('filename', type=str, required=True)
        args = req_parser.parse_args()
        LOGGER.debug("FileUpload GET args: {}".format(args))

        bucket = _get_storage_bucket()

        blob = bucket.blob(args['filename'])
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(temp.name, as_attachment=True, attachment_filename=args['filename'], mimetype='application/pdf')



class FileAPIImproved(FileUploadMixin, restful.Resource):

    def get(self):
        args = self.get_req_parser.parse_args()
        file_id = args['file_id']

        file = file_repository.get_by_id(file_id)

        bucket = _get_storage_bucket()
        blob = bucket.blob(file.guid)        

        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(temp.name, as_attachment=True, attachment_filename=file.file_name, mimetype=file.mime_type)


    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        uploaded_file = args['file']
        
        bytes_file = uploaded_file.read()
        file_size = len(bytes_file)
        if file_size > FILE_SIZE_LIMIT:
            return FILE_SIZE_EXCEEDED

        file = File(uploaded_file)

        bucket = _get_storage_bucket()
        blob = bucket.blob(file.guid)
        blob.upload_from_string(bytes_file, content_type=file.mime_type)

        file_id = file_repository.save(file)

        return {
            'file_id': file_id,
        }, 201