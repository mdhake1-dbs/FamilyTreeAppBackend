from flask import Blueprint, request, jsonify, g
from datetime import datetime
import os
from werkzeug.utils import secure_filename

from ..database import get_db_connection
from ..auth_utils import require_auth
from ..utils.uploads import allowed_file

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/profile-photo', methods=['POST'])
@require_auth
def upload_profile_photo():
    """Upload or update user profile photo."""
    try:
        file = request.files.get('photo')

        if not file or not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file'}), 400

        user_id = g.current_user['id']
        user_dir = f'uploads/users/{user_id}'
        os.makedirs(user_dir, exist_ok=True)

        filename = secure_filename(file.filename)
        path = os.path.join(user_dir, filename)
        file.save(path)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Users
            SET profile_photo = ?, updated_at = ?
            WHERE id = ?
            """,
            (path, datetime.now().isoformat(), user_id)
        )
        conn.commit()

        return jsonify({
            'success': True,
            'profile_photo': path
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/deactivate', methods=['POST'])
@require_auth
def deactivate_account():
    """Deactivate user account."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE Users
            SET is_active = 0, updated_at = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), g.current_user['id'])
        )
        conn.commit()

        return jsonify({'success': True, 'message': 'Account deactivated'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

