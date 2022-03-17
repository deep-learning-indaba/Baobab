"""Gunicorn configuration."""

forwarded_allow_ips = "*"
secure_scheme_headers = {"X-Forwarded-Proto": "https"}
workers = 4
