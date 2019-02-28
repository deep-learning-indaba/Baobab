import uuid

import flask_restful as restful
from flask_restful import reqparse
from config import GCP_CREDENTIALS_DICT, GCP_PROJECT_NAME, GCP_BUCKET_NAME, FILE_SIZE_LIMIT
from app.utils.errors import FILE_SIZE_EXCEEDED

from app.files.mixins import FileUploadMixin
from app.utils.auth import auth_required

from google.cloud import storage
from google.oauth2 import service_account

class FileUploadAPI(FileUploadMixin, restful.Resource):
    
    @auth_required
    def post(self):
        args = self.req_parser.parse_args()

        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )

        storage_client = storage.Client(credentials=credentials, project=GCP_PROJECT_NAME)
        bucket = storage_client.get_bucket(GCP_BUCKET_NAME)
        unique_name = str(uuid.uuid4().hex)
        blob = bucket.blob(unique_name)

        file = args['file']
        bytes_file = file.read()
        content_type = file.content_type
        file_size = len(bytes_file) 

        if file_size > FILE_SIZE_LIMIT:
            return FILE_SIZE_EXCEEDED

        blob.upload_from_string(bytes_file, content_type=content_type)

        return {
            'file_id': unique_name,
        }, 201