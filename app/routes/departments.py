from flask import Blueprint, request, jsonify
from db import get_connection
from rbac import login_required, admin_required
import datetime
import json
import os

departments_bp = Blueprint('departments', __name__)

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


# GET ALL DEPARTMENTS
@departments_bp.route("/departments", methods=["GET"])
@login_required
def get_departments():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.department_id, d.department_name, d.building,
                   d.opening_hours, d.closing_hours,
                   m.member_name AS hod_name
            FROM Department d
            LEFT JOIN Member m ON d.hod_member_id = m.member_id
        """)
        departments = cursor.fetchall()
        cursor.close()
        conn.close()

        for dept in departments:
            for key, value in dept.items():
                if hasattr(value, 'isoformat'):
                    dept[key] = value.isoformat()
                elif hasattr(value, 'seconds'):  # timedelta fix
                    total = int(value.total_seconds())
                    dept[key] = f"{total//3600:02d}:{(total%3600)//60:02d}:00"

        return jsonify(departments), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET SINGLE DEPARTMENT
@departments_bp.route("/departments/<int:department_id>", methods=["GET"])
@login_required
def get_department(department_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT d.department_id, d.department_name, d.building,
                   d.opening_hours, d.closing_hours,
                   m.member_name AS hod_name
            FROM Department d
            LEFT JOIN Member m ON d.hod_member_id = m.member_id
            WHERE d.department_id = %s
        """, (department_id,))
        dept = cursor.fetchone()
        cursor.close()
        conn.close()

        if not dept:
            return jsonify({"error": "Department not found"}), 404

        for key, value in dept.items():
            if hasattr(value, 'isoformat'):
                dept[key] = value.isoformat()

        return jsonify(dept), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#ADD DEPARTMENT (Admin only)
@departments_bp.route("/departments", methods=["POST"])
@admin_required
def add_department():
    data = request.get_json()
    required = ["department_name", "building", "opening_hours", "closing_hours"]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Department (department_name, building, opening_hours, closing_hours)
            VALUES (%s, %s, %s, %s)
        """, (
            data["department_name"],
            data["building"],
            data["opening_hours"],
            data["closing_hours"]
        ))
        new_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        write_audit_log(
            performed_by=request.user["member_id"],
            action_type="INSERT",
            table="Department",
            row_pk=new_id,
            new_data=data
        )

        return jsonify({"message": "Department added successfully", "department_id": new_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# UPDATE DEPARTMENT (Admin only)
@departments_bp.route("/departments/<int:department_id>", methods=["PUT"])
@admin_required
def update_department(department_id):
    data = request.get_json()

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Department WHERE department_id = %s", (department_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({"error": "Department not found"}), 404

        cursor.execute("""
            UPDATE Department
            SET department_name = %s,
                building = %s,
                opening_hours = %s,
                closing_hours = %s
            WHERE department_id = %s
        """, (
            data.get("department_name", old["department_name"]),
            data.get("building", old["building"]),
            data.get("opening_hours", old["opening_hours"]),
            data.get("closing_hours", old["closing_hours"]),
            department_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

        old_serialized = {k: str(v) for k, v in old.items()}

        write_audit_log(
            performed_by=request.user["member_id"],
            action_type="UPDATE",
            table="Department",
            row_pk=department_id,
            old_data=old_serialized,
            new_data=data
        )

        return jsonify({"message": "Department updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# DELETE DEPARTMENT (Admin only) 
@departments_bp.route("/departments/<int:department_id>", methods=["DELETE"])
@admin_required
def delete_department(department_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Department WHERE department_id = %s", (department_id,))
        old = cursor.fetchone()
        if not old:
            return jsonify({"error": "Department not found"}), 404

        # Check if any active members exist in this department
        cursor.execute("""
            SELECT COUNT(*) as count FROM Member
            WHERE department_id = %s AND exit_date IS NULL
        """, (department_id,))
        result = cursor.fetchone()

        if result["count"] > 0:
            return jsonify({
                "error": "Cannot delete department with active members"
            }), 400

        cursor.execute("DELETE FROM Department WHERE department_id = %s", (department_id,))
        conn.commit()
        cursor.close()
        conn.close()

        old_serialized = {k: str(v) for k, v in old.items()}

        write_audit_log(
            performed_by=request.user["member_id"],
            action_type="DELETE",
            table="Department",
            row_pk=department_id,
            old_data=old_serialized
        )

        return jsonify({"message": "Department deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500