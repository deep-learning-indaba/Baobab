from app.organisation.repository import OrganisationRepository
from app.organisation.models import PlainOrganisation
from app.utils.auth import verify_payload
from app import LOGGER
from flask import request
import time
from werkzeug.exceptions import BadRequest

# Bounds how stale an instance's cache can be after another instance edits an organisation.
ORGANISATION_CACHE_TTL_SECONDS = 60

class OrganisationResolver():
    _cache = None
    _loaded_at = None

    @classmethod
    def _populate_cache(cls):
        LOGGER.info('Populating Organisation Cache')
        organisations = OrganisationRepository.get_all()
        cls._cache = {}
        for org in organisations:
            cls._cache[org.domain] = PlainOrganisation.from_organisation_model(org)
        cls._loaded_at = time.monotonic()

    @classmethod
    def reset_cache(cls):
        cls._cache = None
        cls._loaded_at = None

    @classmethod
    def bust_cache(cls):
        cls._populate_cache()

    @classmethod
    def _cache_expired(cls):
        return cls._loaded_at is None or time.monotonic() - cls._loaded_at > ORGANISATION_CACHE_TTL_SECONDS

    @classmethod
    def resolve_from_domain(cls, domain):
        if not cls._cache or cls._cache_expired():
            cls._populate_cache()
        
        if domain not in cls._cache:
            # Re-populate the cache and retry
            cls._populate_cache()
            LOGGER.warning('Could not resolve organisation from domain: {}, trying to repopulate cache'.format(domain))
            if domain not in cls._cache:
                LOGGER.error('Could not resolve organisation from domain: {}, HTTP Origin: {}, HTTP Referer: {}'.format(
                    domain, request.environ.get('HTTP_ORIGIN', ''), request.environ.get('HTTP_REFERER', '')))
                raise BadRequest('Could not resolve organisation')
        
        return cls._cache[domain]
    
    @classmethod
    def resolve_from_stripe_signature(cls, signed_payload: str, expected_signature: str):
        if not cls._cache or cls._cache_expired():
            cls._populate_cache()
        
        for org in cls._cache.values():
            secret = org.stripe_webhook_secret_key
            if secret:
                if verify_payload(signed_payload, secret, expected_signature):
                    return org
        
        raise BadRequest('Could not resolve organisation from stripe signature')
    

