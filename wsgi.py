"""WSGI entrypoint for Gunicorn."""

from backend.api.app import create_app

app = create_app()
