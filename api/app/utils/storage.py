"""Utilities for interaction with Google Cloud Storage, and a mock version of it for loal development."""

import os

import requests
import urllib3
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from google.oauth2 import service_account

from app import LOGGER
from config import GCP_BUCKET_NAME, GCP_CREDENTIALS_DICT, GCP_PROJECT_NAME


def _create_dummy_storage_client():
    fake_host = "storage"
    external_url = "https://{}:4443".format(fake_host)
    storage.blob._API_ACCESS_ENDPOINT = "https://storage.gcs.{}.nip.io:4443".format(
        fake_host
    )
    storage.blob._DOWNLOAD_URL_TEMPLATE = (
        "%s/download/storage/v1{path}?alt=media" % external_url
    )
    storage.blob._BASE_UPLOAD_TEMPLATE = (
        "%s/upload/storage/v1{bucket_path}/o?uploadType=" % external_url
    )
    storage.blob._MULTIPART_URL_TEMPLATE = (
        storage.blob._BASE_UPLOAD_TEMPLATE + "multipart"
    )
    storage.blob._RESUMABLE_URL_TEMPLATE = (
        storage.blob._BASE_UPLOAD_TEMPLATE + "resumable"
    )
    my_http = requests.Session()
    my_http.verify = False  # disable SSL validation
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )  # disable https warnings for https insecure certs

    storage_client = storage.Client(
        credentials=AnonymousCredentials(),
        project="test",
        _http=my_http,
        client_options=ClientOptions(api_endpoint=external_url),
    )

    if len(list(storage_client.list_buckets())) == 0:
        bucket = storage_client.create_bucket(_get_bucket_name())

    return storage_client


def _create_real_storage_client():
    if GCP_CREDENTIALS_DICT["private_key"] == "dummy":
        # Running on GCP, so no credentials needed
        storage_client = storage.Client(project=GCP_PROJECT_NAME)
    else:
        # Create credentials to access from anywhere
        credentials = service_account.Credentials.from_service_account_info(
            GCP_CREDENTIALS_DICT
        )
        storage_client = storage.Client(
            credentials=credentials, project=GCP_PROJECT_NAME
        )
    return storage_client


def _get_bucket_name():
    # return 'LocalBucket' if GCP_CREDENTIALS_DICT['private_key'] == 'dummy' else GCP_BUCKET_NAME
    return GCP_BUCKET_NAME


def _get_storage_bucket(storage_client):
    return storage_client.get_bucket(_get_bucket_name())


def get_storage_bucket():
    LOGGER.debug("Setting GCP storage client")
    storage_client = _create_real_storage_client()

    return _get_storage_bucket(storage_client)
