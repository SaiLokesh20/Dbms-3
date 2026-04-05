from flask import Blueprint, request, jsonify
from db import get_connection
from rbac import login_required, admin_required
import datetime

analytics_bp = Blueprint('analytics', __name__)


# LOG A SEARCH (any logged in user)
@analytics_bp.route("/search", methods=["POST"])
@login_required
def log_search():
    data = request.get_json()
    if "search_keyword" not in data:
        return jsonify({"error": "Missing search_keyword"}), 400

    keyword = data["search_keyword"]
    filter_dept = data.get("filter_department_id", None)
    filter_role = data.get("filter_role_id", None)
    page = int(data.get("page", 1))
    limit = int(data.get("limit", 20))
    offset = (page - 1) * limit

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
                   d.department_name, r.role_name
            FROM Member m
            JOIN Department d ON m.department_id = d.department_id
            JOIN Member_Role mr ON m.member_id = mr.member_id
            JOIN Role r ON mr.role_id = r.role_id
            WHERE mr.is_primary = TRUE AND m.exit_date IS NULL
            AND (m.member_name LIKE %s OR m.iit_email LIKE %s)
        """
        params = [f"%{keyword}%", f"%{keyword}%"]

        if filter_dept:
            query += " AND m.department_id = %s"
            params.append(filter_dept)
        if filter_role:
            query += " AND mr.role_id = %s"
            params.append(filter_role)

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as sub"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Get paginated results
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cursor.execute(query, params)
        results = cursor.fetchall()
        result_count = len(results)

        # Log the search
        cursor.execute("""
            INSERT INTO Search_Log
            (member_id, search_keyword, search_time, result_count, filter_department_id, filter_role_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (request.user["member_id"], keyword, datetime.datetime.now(), total, filter_dept, filter_role))

        conn.commit()
        cursor.close()
        conn.close()

        for r in results:
            for key, value in r.items():
                if hasattr(value, 'isoformat'):
                    r[key] = value.isoformat()

        return jsonify({
            "results": results,
            "result_count": result_count,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LOG CALL OR EMAIL INTERACTION
@analytics_bp.route("/interact", methods=["POST"])
@login_required
def log_interaction():
    data = request.get_json()

    if "target_member_id" not in data or "interaction_type" not in data:
        return jsonify({"error": "Missing fields"}), 400

    valid_types = ["VIEW_PROFILE", "CLICK_CALL", "CLICK_EMAIL"]
    if data["interaction_type"] not in valid_types:
        return jsonify({"error": "Invalid interaction type"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Directory_Interaction_Log
            (actor_member_id, target_member_id, interaction_type, interaction_time)
            VALUES (%s, %s, %s, %s)
        """, (
            request.user["member_id"],
            data["target_member_id"],
            data["interaction_type"],
            datetime.datetime.now()
        ))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Interaction logged"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET ANALYTICS (Admin only)
@analytics_bp.route("/analytics", methods=["GET"])
@admin_required
def get_analytics():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Most searched keywords
        cursor.execute("""
            SELECT search_keyword, COUNT(*) as search_count
            FROM Search_Log
            GROUP BY search_keyword
            ORDER BY search_count DESC
            LIMIT 5
        """)
        top_searches = cursor.fetchall()

        # Most contacted departments
        cursor.execute("""
            SELECT d.department_name, COUNT(*) as contact_count
            FROM Directory_Interaction_Log dil
            JOIN Member m ON dil.target_member_id = m.member_id
            JOIN Department d ON m.department_id = d.department_id
            WHERE dil.interaction_type IN ('CLICK_CALL', 'CLICK_EMAIL')
            GROUP BY d.department_name
            ORDER BY contact_count DESC
            LIMIT 5
        """)
        top_departments = cursor.fetchall()

        # Most viewed profiles
        cursor.execute("""
            SELECT m.member_name, m.iit_email, COUNT(*) as view_count
            FROM Directory_Interaction_Log dil
            JOIN Member m ON dil.target_member_id = m.member_id
            WHERE dil.interaction_type = 'VIEW_PROFILE'
            GROUP BY m.member_id
            ORDER BY view_count DESC
            LIMIT 5
        """)
        top_profiles = cursor.fetchall()

        # Recent audit logs
        cursor.execute("""
            SELECT a.action_type, a.affected_table, a.action_time,
                   m.member_name AS performed_by
            FROM Audit_Log a
            JOIN Member m ON a.performed_by_member_id = m.member_id
            ORDER BY a.action_time DESC
            LIMIT 10
        """)
        recent_audits = cursor.fetchall()

        cursor.close()
        conn.close()

        for item in recent_audits:
            for key, value in item.items():
                if hasattr(value, 'isoformat'):
                    item[key] = value.isoformat()

        return jsonify({
            "top_searches": top_searches,
            "top_departments": top_departments,
            "top_profiles": top_profiles,
            "recent_audits": recent_audits
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET LOGIN HISTORY (Admin only)
@analytics_bp.route("/login-history", methods=["GET"])
@admin_required
def get_login_history():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT lh.login_id, m.member_name, m.iit_email,
                   lh.login_time, lh.logout_time, lh.ip_address
            FROM Login_History lh
            JOIN Member m ON lh.member_id = m.member_id
            ORDER BY lh.login_time DESC
            LIMIT 20
        """)
        history = cursor.fetchall()
        cursor.close()
        conn.close()

        for item in history:
            for key, value in item.items():
                if hasattr(value, 'isoformat'):
                    item[key] = value.isoformat()

        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500