#!/usr/bin/python3

from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

from backend.config import Config
from backend.database import init_db, close_db_connection
from backend.routes import register_routes

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)

# Initialize database
init_db(app)

# Register all routes
register_routes(app)

# Teardown database connection
app.teardown_appcontext(close_db_connection)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    upload_dir = app.config.get('UPLOAD_FOLDER')
    if not upload_dir:
        abort(500, "UPLOAD_FOLDER not configured")

    full_path = os.path.join(upload_dir, filename)
    if not os.path.isfile(full_path):
        abort(404)

    return send_from_directory(upload_dir, filename)

if __name__ == '__main__':
    # Ensure database directory exists
    db_dir = os.path.dirname(app.config['DB_PATH'])
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=80)
