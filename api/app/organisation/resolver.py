from app.organisation.repository import OrganisationRepository
from app.utils.auth import verify_payload
from app import LOGGER
from flask import request
from werkzeug.exceptions import BadRequest

class OrganisationResolver():
    _cache = None
    _secrets_cache = None

    @classmethod
    def _populate_cache(cls):
        LOGGER.info('Populating Organisation Cache')
        organisations = OrganisationRepository.get_all()
        cls._cache = {}
        cls._secrets_cache = {}
        for org in organisations:
            cls._cache[org.domain] = org
            cls._secrets_cache[org.domain] = org.stripe_webhook_secret_key

    @classmethod
    def resolve_from_domain(cls, domain):
        if not cls._cache or not cls._secrets_cache:
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
        if not cls._cache or not cls._secrets_cache:
            cls._populate_cache()
        
        for org_domain, secret in cls._secrets_cache.items():
            if secret:
                if verify_payload(signed_payload, secret, expected_signature):
                    return cls._cache[org_domain]
        
        raise BadRequest('Could not resolve organisation from stripe signature')
    

