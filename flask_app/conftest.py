"""
Pytest configuration for flask_app tests.
Adds the flask_app directory to sys.path so imports work without installation.
"""
import sys
import os

# Ensure flask_app root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
