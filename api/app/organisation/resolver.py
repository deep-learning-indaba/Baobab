from app.organisation.repository import OrganisationRepository
from app import LOGGER
from flask import request
from werkzeug.exceptions import BadRequest

class OrganisationResolver():
    _cache = None

    @classmethod
    def resolve_from_domain(cls, domain):
        if not cls._cache:
            LOGGER.info('Populating Organisation Cache')
            organisations = OrganisationRepository.get_all()
            cls._cache = {}
            for org in organisations:
                cls._cache[org.domain] = org
        
        if domain not in cls._cache:
            LOGGER.error('Could not resolve organisation from domain: {}, HTTP Origin: {}, HTTP Referer: {}'.format(
                domain, request.environ.get('HTTP_ORIGIN', ''), request.environ.get('HTTP_REFERER', '')))
            raise BadRequest('Could not resolve organisation')
        else:    
            return cls._cache[domain]
