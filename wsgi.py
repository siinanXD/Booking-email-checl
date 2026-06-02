"""WSGI entrypoint for Gunicorn."""

from web.app import create_app

app = create_app()
