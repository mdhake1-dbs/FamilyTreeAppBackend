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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Ensure database directory exists
    db_dir = os.path.dirname(app.config['DB_PATH'])
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=80)
