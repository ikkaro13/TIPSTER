import sys
import os

# Añadimos el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from main import app
from a2wsgi import ASGIMiddleware

# PythonAnywhere busca por defecto la variable "application"
application = ASGIMiddleware(app)
