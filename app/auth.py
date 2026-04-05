from flask import Blueprint, request, jsonify
import jwt
import datetime
import os
from db import get_connection

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = "callhub_secret_key"


def generate_token(member_id, role_name):
    payload = {
        "member_id": member_id,
        "role": role_name,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Missing parameters"}), 401

    email = data["email"]
    password = data["password"]

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
                   r.role_name
            FROM Member m
            JOIN Member_Role mr ON m.member_id = mr.member_id
            JOIN Role r ON mr.role_id = r.role_id
            WHERE m.iit_email = %s AND mr.is_primary = TRUE
        """, (email,))

        member = cursor.fetchone()

        if not member:
            return jsonify({"error": "Invalid credentials"}), 401

        # Password is primary_phone
        if password != member["primary_phone"]:
            return jsonify({"error": "Invalid credentials"}), 401

        # Log login to Login_History
        cursor.execute("""
            INSERT INTO Login_History (member_id, login_time, ip_address)
            VALUES (%s, %s, %s)
        """, (
            member["member_id"],
            datetime.datetime.now(),
            request.remote_addr
        ))

        login_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        token = generate_token(member["member_id"], member["role_name"])

        return jsonify({
            "message": "Login successful",
            "session_token": token,
            "member_id": member["member_id"],
            "name": member["member_name"],
            "role": member["role_name"],
            "login_id": login_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/isAuth", methods=["GET"])
def is_auth():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "No session found"}), 401

    payload = verify_token(token)

    if not payload:
        return jsonify({"error": "Session expired or invalid"}), 401

    return jsonify({
        "message": "User is authenticated",
        "member_id": payload["member_id"],
        "role": payload["role"],
        "expiry": str(payload["exp"])
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")

    if token:
        payload = verify_token(token)
        if payload:
            login_id = request.get_json().get("login_id") if request.get_json() else None
            if login_id:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE Login_History
                        SET logout_time = %s
                        WHERE login_id = %s
                    """, (datetime.datetime.now(), login_id))
                    conn.commit()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    print("Logout log error:", e)

    return jsonify({"message": "Logged out successfully"}), 200