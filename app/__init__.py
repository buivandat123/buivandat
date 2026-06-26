# app/__init__.py
# -*- coding: utf-8 -*-
import os
from flask import Flask

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'app/templates'),
    static_folder=os.path.join(BASE_DIR, 'app/static')
)
app.secret_key = "zbug_secret_key_2024"

from app.core import server
