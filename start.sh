#!/bin/bash

# This script is used to start the Flask application with Gunicorn.

# Activate your Python environment if you have one
# Uncomment and modify the following line if using a virtual environment
# source /path/to/your/venv/bin/activate

# Run the Flask application with Gunicorn
# Replace 'app:app' with your actual Flask application module and instance
gunicorn --bind 0.0.0.0:8000 app:app