from app.organisation.repository import OrganisationRepository
from app import LOGGER

class OrganisationResolver():
    _cache = None
    _default = None

    @classmethod
    def resolve_from_domain(cls, domain):
        if not cls._cache:
            LOGGER.info('Populating Organisation Cache')
            organisations = OrganisationRepository.get_all()
            cls._cache = {}
            for org in organisations:
                cls._cache[org.domain] = org
                if org.is_default:
                    cls._default = org
        
        if domain not in cls._cache:
            LOGGER.warning('Could not find domain {} in cache, returning default organisation'.format(domain))
            return cls._default
        else:    
            return cls._cache[domain]
