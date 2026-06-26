# app/core/server/__init__.py
from .server import Open, Run
from .libs import app
from .api import *
from .live import *

def init_routes(app):
    """Khởi tạo routes cho app Flask"""
    return app
