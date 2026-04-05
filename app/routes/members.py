from flask import Blueprint, request, jsonify
from db import get_connection
from rbac import login_required, admin_required, is_admin
import datetime
import json
import os

members_bp = Blueprint('members', __name__)

# Path to audit log file
AUDIT_LOG_PATH = os.path.join(os.path.dirname(__file__), '../../logs/audit.log')

def write_audit_log(performed_by, target_id, action_type, table, row_pk, old_data=None, new_data=None):
    # Write to audit.log file
    log_entry = {
        "time": str(datetime.datetime.now()),
        "performed_by": performed_by,
        "target_id": target_id,
        "action": action_type,
        "table": table,
        "row_pk": row_pk,
        "old_data": old_data,
        "new_data": new_data
    }
    with open(AUDIT_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    # write to Audit_Log table in DB
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Audit_Log 
            (performed_by_member_id, target_member_id, action_type, 
             affected_table, affected_row_pk, old_data, new_data, action_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            performed_by,
            target_id,
            action_type,
            table,
            str(row_pk),
            json.dumps(old_data) if old_data else None,
            json.dumps(new_data) if new_data else None,
            datetime.datetime.now()
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Audit DB log error:", e)


# GET ALL MEMBERS 
@members_bp.route("/members", methods=["GET"])
@login_required
def get_members():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 20))
        offset = (page - 1) * limit

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) as total FROM Member m
            JOIN Member_Role mr ON m.member_id = mr.member_id
            WHERE mr.is_primary = TRUE AND m.exit_date IS NULL
        """)
        total = cursor.fetchone()["total"]

        # Get paginated members
        cursor.execute("""
            SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
                   m.is_at_campus, m.join_date, m.exit_date,
                   d.department_name, r.role_name
            FROM Member m
            JOIN Department d ON m.department_id = d.department_id
            JOIN Member_Role mr ON m.member_id = mr.member_id
            JOIN Role r ON mr.role_id = r.role_id
            WHERE mr.is_primary = TRUE AND m.exit_date IS NULL
            LIMIT %s OFFSET %s
        """, (limit, offset))

        members = cursor.fetchall()
        cursor.close()
        conn.close()

        for member in members:
            for key, value in member.items():
                if hasattr(value, 'isoformat'):
                    member[key] = value.isoformat()

        return jsonify({
            "members": members,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# GET SINGLE MEMBER 
@members_bp.route("/members/<int:member_id>", methods=["GET"])
@login_required
def get_member(member_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
                   m.dob, m.is_at_campus, m.join_date, m.exit_date,
                   d.department_name, r.role_name
            FROM Member m
            JOIN Department d ON m.department_id = d.department_id
            JOIN Member_Role mr ON m.member_id = mr.member_id
            JOIN Role r ON mr.role_id = r.role_id
            WHERE m.member_id = %s AND mr.is_primary = TRUE
        """, (member_id,))
        member = cursor.fetchone()
        cursor.close()
        conn.close()

        if not member:
            return jsonify({"error": "Member not found"}), 404

        for key, value in member.items():
            if hasattr(value, 'isoformat'):
                member[key] = value.isoformat()

        return jsonify(member), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ADD NEW MEMBER (Admin only)
@members_bp.route("/members", methods=["POST"])
@admin_required
def add_member():
    data = request.get_json()
    required = ["member_name", "iit_email", "primary_phone", "dob", "department_id", "join_date", "role_id"]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Member 
            (member_name, iit_email, primary_phone, dob, department_id, is_at_campus, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data["member_name"],
            data["iit_email"],
            data["primary_phone"],
            data["dob"],
            data["department_id"],
            data.get("is_at_campus", True),
            data["join_date"]
        ))

        new_member_id = cursor.lastrowid

        # Assign role
        cursor.execute("""
            INSERT INTO Member_Role (member_id, role_id, is_primary, start_date)
            VALUES (%s, %s, TRUE, %s)
        """, (new_member_id, data["role_id"], data["join_date"]))

        conn.commit()
        cursor.close()
        conn.close()

        write_audit_log(
            performed_by=request.user["member_id"],
            target_id=new_member_id,
            action_type="INSERT",
            table="Member",
            row_pk=new_member_id,
            new_data=data
        )

        return jsonify({"message": "Member added successfully", "member_id": new_member_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# UPDATE MEMBER (Admin only) 
@members_bp.route("/members/<int:member_id>", methods=["PUT"])
@admin_required
def update_member(member_id):
    data = request.get_json()

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get old data first for audit
        cursor.execute("SELECT * FROM Member WHERE member_id = %s", (member_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({"error": "Member not found"}), 404

        cursor.execute("""
            UPDATE Member
            SET member_name = %s,
                primary_phone = %s,
                is_at_campus = %s
            WHERE member_id = %s
        """, (
            data.get("member_name", old["member_name"]),
            data.get("primary_phone", old["primary_phone"]),
            data.get("is_at_campus", old["is_at_campus"]),
            member_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        old_serialized = {k: str(v) for k, v in old.items()}

        write_audit_log(
            performed_by=request.user["member_id"],
            target_id=member_id,
            action_type="UPDATE",
            table="Member",
            row_pk=member_id,
            old_data=old_serialized,
            new_data=data
        )

        return jsonify({"message": "Member updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# DELETE MEMBER (Admin only)
@members_bp.route("/members/<int:member_id>", methods=["DELETE"])
@admin_required
def delete_member(member_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Member WHERE member_id = %s", (member_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({"error": "Member not found"}), 404

        # Soft delete — just set exit_date
        cursor.execute("""
            UPDATE Member SET exit_date = %s WHERE member_id = %s
        """, (datetime.date.today(), member_id))

        conn.commit()
        cursor.close()
        conn.close()

        old_serialized = {k: str(v) for k, v in old.items()}

        write_audit_log(
            performed_by=request.user["member_id"],
            target_id=member_id,
            action_type="DELETE",
            table="Member",
            row_pk=member_id,
            old_data=old_serialized
        )

        return jsonify({"message": "Member deactivated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500