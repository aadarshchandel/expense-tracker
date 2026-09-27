from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path so we can import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

# Import the Handler class from app.py
from app import Handler


# Vercel requires the class to be named "handler" (lowercase)
class handler(Handler):
    pass