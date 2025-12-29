from flask import Blueprint, request, jsonify, g
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

from ..database import get_db_connection
from ..auth_utils import require_auth

people_bp = Blueprint('people', __name__, url_prefix='/api/people')


def save_resized_image(file, path, size=(256, 256), quality=75):
    try:
        img = Image.open(file)
    except UnidentifiedImageError:
        raise ValueError("Uploaded file is not a valid image")

    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert("RGB")

    img.thumbnail(size)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format="JPEG", quality=quality, optimize=True)


@people_bp.route('/<int:person_id>/photo', methods=['POST'])
@require_auth
def upload_person_photo(person_id):
    file = request.files.get('photo')
    if not file:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    base_upload_dir = "/app/uploads/people"
    filename = "photo.jpg"
    full_path = os.path.join(base_upload_dir, str(person_id), filename)

    try:
        save_resized_image(file, full_path)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    db_path = f"uploads/people/{person_id}/{filename}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE People
        SET photo = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (db_path, datetime.now().isoformat(), person_id, g.current_user['id']))
    conn.commit()

    return jsonify({'success': True, 'photo': db_path}), 200


@people_bp.route('', methods=['GET'])
@require_auth
def get_all_people():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id, given_name, family_name, photo, other_names, gender,
            birth_date, death_date,
            birth_place, birth_lat, birth_lng,
            bio, relation,
            created_at, updated_at
        FROM People
        WHERE is_deleted = 0 AND user_id = ?
        ORDER BY family_name, given_name
    """, (g.current_user['id'],))
    rows = cur.fetchall()
    return jsonify({'success': True, 'data': [dict(r) for r in rows]}), 200


@people_bp.route('/<int:person_id>', methods=['GET'])
@require_auth
def get_person(person_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            id, given_name, family_name, photo, other_names, gender,
            birth_date, death_date,
            birth_place, birth_lat, birth_lng,
            bio, relation,
            created_at, updated_at
        FROM People
        WHERE id = ? AND is_deleted = 0 AND user_id = ?
    """, (person_id, g.current_user['id']))
    row = cur.fetchone()

    if not row:
        return jsonify({'success': False, 'error': 'Person not found'}), 404

    return jsonify({'success': True, 'data': dict(row)}), 200


@people_bp.route('', methods=['POST'])
@require_auth
def create_person():
    data = request.get_json() or {}

    if not data.get('given_name') or not data.get('family_name'):
        return jsonify({'success': False, 'error': 'Given name and family name are required'}), 400

    now = datetime.now().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO People (
            given_name, family_name, other_names, gender,
            birth_date, death_date,
            birth_place, birth_lat, birth_lng,
            bio, relation,
            created_at, updated_at, is_deleted, user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (
        data.get('given_name'),
        data.get('family_name'),
        data.get('other_names'),
        data.get('gender'),
        data.get('birth_date'),
        data.get('death_date'),
        data.get('birth_place'),
        data.get('birth_lat'),
        data.get('birth_lng'),
        data.get('bio'),
        data.get('relation'),
        now,
        now,
        g.current_user['id']
    ))
    conn.commit()

    return jsonify({'success': True, 'id': cur.lastrowid}), 201


@people_bp.route('/<int:person_id>', methods=['PUT'])
@require_auth
def update_person(person_id):
    data = request.get_json() or {}
    now = datetime.now().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE People SET
            given_name = ?,
            family_name = ?,
            other_names = ?,
            gender = ?,
            birth_date = ?,
            death_date = ?,
            birth_place = ?,
            birth_lat = ?,
            birth_lng = ?,
            bio = ?,
            relation = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ? AND is_deleted = 0
    """, (
        data.get('given_name'),
        data.get('family_name'),
        data.get('other_names'),
        data.get('gender'),
        data.get('birth_date'),
        data.get('death_date'),
        data.get('birth_place'),
        data.get('birth_lat'),
        data.get('birth_lng'),
        data.get('bio'),
        data.get('relation'),
        now,
        person_id,
        g.current_user['id']
    ))
    conn.commit()

    return jsonify({'success': True, 'message': 'Person updated successfully'}), 200


@people_bp.route('/<int:person_id>', methods=['DELETE'])
@require_auth
def delete_person(person_id):
    now = datetime.now().isoformat()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE People
        SET is_deleted = 1, updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (now, person_id, g.current_user['id']))
    conn.commit()

    return jsonify({'success': True, 'message': 'Person deleted successfully'}), 200

