from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..database import get_db_connection
from ..auth_utils import require_auth

events_bp = Blueprint('events', __name__, url_prefix='/api/events')


@events_bp.route('', methods=['GET'])
@require_auth
def list_events():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            e.title,
            e.event_date,
            e.place,
            e.place_lat,
            e.place_lng,
            e.description,
            e.created_by,
            p.given_name || ' ' || p.family_name AS person_name
        FROM Events e
        LEFT JOIN People p ON e.created_by = p.id
        WHERE e.user_id = ?
        ORDER BY e.event_date IS NULL, e.event_date DESC, e.id DESC
    """, (g.current_user['id'],))

    rows = cur.fetchall()
    data = [dict(row) for row in rows]

    return jsonify({'success': True, 'data': data}), 200


@events_bp.route('', methods=['POST'])
@require_auth
def create_event():
    data = request.get_json() or {}

    person_id = data.get('created_by')
    title = data.get('title', '').strip()

    if not person_id or not title:
        return jsonify({'success': False, 'error': 'Person and title are required'}), 400

    now = datetime.now().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Events (
            title,
            event_date,
            place,
            place_lat,
            place_lng,
            description,
            created_by,
            user_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        data.get('event_date'),
        data.get('place'),
        data.get('place_lat'),
        data.get('place_lng'),
        data.get('description'),
        person_id,
        g.current_user['id'],
        now,
        now
    ))

    conn.commit()

    return jsonify({'success': True, 'id': cur.lastrowid}), 201


@events_bp.route('/<int:event_id>', methods=['GET'])
@require_auth
def get_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            e.title,
            e.event_date,
            e.place,
            e.place_lat,
            e.place_lng,
            e.description,
            e.created_by,
            p.given_name || ' ' || p.family_name AS person_name
        FROM Events e
        LEFT JOIN People p ON e.created_by = p.id
        WHERE e.id = ? AND e.user_id = ?
    """, (event_id, g.current_user['id']))

    row = cur.fetchone()

    if not row:
        return jsonify({'success': False, 'error': 'Event not found'}), 404

    event = dict(row)

    return jsonify({'success': True, 'data': event}), 200


@events_bp.route('/<int:event_id>', methods=['PUT'])
@require_auth
def update_event(event_id):
    data = request.get_json() or {}

    person_id = data.get('created_by')
    title = data.get('title', '').strip()

    if not person_id or not title:
        return jsonify({'success': False, 'error': 'Person and title are required'}), 400

    now = datetime.now().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE Events SET
            title = ?,
            event_date = ?,
            place = ?,
            place_lat = ?,
            place_lng = ?,
            description = ?,
            created_by = ?,
            updated_at = ?
        WHERE id = ? AND user_id = ?
    """, (
        title,
        data.get('event_date'),
        data.get('place'),
        data.get('place_lat'),
        data.get('place_lng'),
        data.get('description'),
        person_id,
        now,
        event_id,
        g.current_user['id']
    ))

    conn.commit()

    if cur.rowcount == 0:
        return jsonify({'success': False, 'error': 'Event not found'}), 404

    return jsonify({'success': True, 'message': 'Event updated successfully'}), 200


@events_bp.route('/<int:event_id>', methods=['DELETE'])
@require_auth
def delete_event(event_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM Events
        WHERE id = ? AND user_id = ?
    """, (event_id, g.current_user['id']))

    conn.commit()

    if cur.rowcount == 0:
        return jsonify({'success': False, 'error': 'Event not found'}), 404

    return jsonify({'success': True, 'message': 'Event deleted successfully'}), 200

