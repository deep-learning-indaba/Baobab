"""Gunicorn configuration."""

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}
workers = 2
timeout = 120
preload_app = True
capture_output = True
loglevel = 'debug'
errorlog = '-'
accesslog = '-'
