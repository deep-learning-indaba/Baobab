import logging.config

LOGGING_APPLICATION_CONF = {
    'version': 1,  # required
    'disable_existing_loggers': True,  # this config overrides all other loggers
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s -- %(message)s'
        },
        'sysout': {
            'format': '%(asctime)s\t%(levelname)s -- %(filename)s:%(lineno)s -- %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'sysout'
        }
    },
    'loggers': {
        'app': {  # 'root' logge
            'level': 'DEBUG',
            'handlers': ['console']
        }
    }
}


class Logger:
    '''    
    This class contains methods to use standard loggers
    '''

    def get_logger(self):
        '''This method sets the configuration for the logger
        Returns:
            [Logger] --  An instance of Logging with the right handlers set
        '''

        logging.config.dictConfig(LOGGING_APPLICATION_CONF)
        logger = logging.getLogger('app')
        handlers = logger.handlers
        handler = logging.StreamHandler()
        logger.handlers = []
        logger.addHandler(handlers[0])
        return logger
