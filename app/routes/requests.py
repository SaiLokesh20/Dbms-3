from flask import Blueprint, request, jsonify
from db import get_connection
from rbac import login_required, admin_required
import datetime
import json
import os

requests_bp = Blueprint('requests', __name__)

AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), '../../logs/audit.log')

def write_audit_log(performed_by, action_type, table, row_pk, old_data=None, new_data=None):
    log_entry = {
        "time": str(datetime.datetime.now()),
        "performed_by": performed_by,
        "action": action_type,
        "table": table,
        "row_pk": row_pk,
        "old_data": old_data,
        "new_data": new_data
    }
    with open(AUDIT_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


# ─── SUBMIT EDIT REQUEST (any logged in user) ─────────────
@requests_bp.route("/requests", methods=["POST"])
@login_required
def submit_request():
    data = request.get_json()
    member_id = request.user["member_id"]

    # Check if user already has a pending request
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT request_id FROM Edit_Request
        WHERE member_id = %s AND status = 'PENDING'
    """, (member_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        conn.close()
        return jsonify({"error": "You already have a pending request"}), 400

    # At least one field must be provided
    if not any([data.get("requested_name"), data.get("requested_phone"), data.get("requested_campus") is not None]):
        cursor.close()
        conn.close()
        return jsonify({"error": "Please provide at least one field to change"}), 400

    cursor.execute("""
        INSERT INTO Edit_Request
        (member_id, requested_name, requested_phone, requested_campus, status, requested_at)
        VALUES (%s, %s, %s, %s, 'PENDING', %s)
    """, (
        member_id,
        data.get("requested_name"),
        data.get("requested_phone"),
        data.get("requested_campus"),
        datetime.datetime.now()
    ))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({"message": "Request submitted successfully", "request_id": new_id}), 201


# ─── GET ALL REQUESTS (Admin only) ────────────────────────
@requests_bp.route("/requests", methods=["GET"])
@admin_required
def get_requests():
    status_filter = request.args.get("status", "PENDING")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT er.request_id, er.member_id, m.member_name, m.iit_email,
               er.requested_name, er.requested_phone, er.requested_campus,
               er.status, er.requested_at, er.reviewed_at,
               rv.member_name AS reviewed_by_name
        FROM Edit_Request er
        JOIN Member m ON er.member_id = m.member_id
        LEFT JOIN Member rv ON er.reviewed_by = rv.member_id
        WHERE er.status = %s
        ORDER BY er.requested_at DESC
    """, (status_filter,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        for key, value in row.items():
            if hasattr(value, 'isoformat'):
                row[key] = value.isoformat()

    return jsonify(rows), 200


# ─── GET MY REQUEST (logged in user) ──────────────────────
@requests_bp.route("/requests/my", methods=["GET"])
@login_required
def get_my_request():
    member_id = request.user["member_id"]
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM Edit_Request
        WHERE member_id = %s
        ORDER BY requested_at DESC
        LIMIT 1
    """, (member_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify(None), 200

    for key, value in row.items():
        if hasattr(value, 'isoformat'):
            row[key] = value.isoformat()

    return jsonify(row), 200


# ─── ACCEPT REQUEST (Admin only) ──────────────────────────
@requests_bp.route("/requests/<int:request_id>/accept", methods=["POST"])
@admin_required
def accept_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Edit_Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        conn.close()
        return jsonify({"error": "Request not found"}), 404

    if req["status"] != "PENDING":
        cursor.close()
        conn.close()
        return jsonify({"error": "Request already reviewed"}), 400

    # Get current member data for audit
    cursor.execute("SELECT * FROM Member WHERE member_id = %s", (req["member_id"],))
    old_member = cursor.fetchone()
    old_serialized = {k: str(v) for k, v in old_member.items()}

    # Apply changes
    updates = []
    params = []
    if req["requested_name"]:
        updates.append("member_name = %s")
        params.append(req["requested_name"])
    if req["requested_phone"]:
        updates.append("primary_phone = %s")
        params.append(req["requested_phone"])
    if req["requested_campus"] is not None:
        updates.append("is_at_campus = %s")
        params.append(req["requested_campus"])

    if updates:
        params.append(req["member_id"])
        cursor.execute(f"UPDATE Member SET {', '.join(updates)} WHERE member_id = %s", params)

    # Mark request as accepted
    cursor.execute("""
        UPDATE Edit_Request
        SET status = 'ACCEPTED', reviewed_at = %s, reviewed_by = %s
        WHERE request_id = %s
    """, (datetime.datetime.now(), request.user["member_id"], request_id))

    conn.commit()
    cursor.close()
    conn.close()

    write_audit_log(
        performed_by=request.user["member_id"],
        action_type="UPDATE",
        table="Member",
        row_pk=req["member_id"],
        old_data=old_serialized,
        new_data={"accepted_request_id": request_id}
    )

    return jsonify({"message": "Request accepted and changes applied"}), 200


# ─── REJECT REQUEST (Admin only) ──────────────────────────
@requests_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
@admin_required
def reject_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Edit_Request WHERE request_id = %s", (request_id,))
    req = cursor.fetchone()

    if not req:
        cursor.close()
        conn.close()
        return jsonify({"error": "Request not found"}), 404

    if req["status"] != "PENDING":
        cursor.close()
        conn.close()
        return jsonify({"error": "Request already reviewed"}), 400

    cursor.execute("""
        UPDATE Edit_Request
        SET status = 'REJECTED', reviewed_at = %s, reviewed_by = %s
        WHERE request_id = %s
    """, (datetime.datetime.now(), request.user["member_id"], request_id))

    conn.commit()
    cursor.close()
    conn.close()

    write_audit_log(
        performed_by=request.user["member_id"],
        action_type="UPDATE",
        table="Edit_Request",
        row_pk=request_id,
        new_data={"status": "REJECTED"}
    )

    return jsonify({"message": "Request rejected"}), 200