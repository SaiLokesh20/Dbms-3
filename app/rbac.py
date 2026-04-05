from functools import wraps
from flask import request, jsonify
from auth import verify_token
import datetime

# These roles are considered Admins in CallHub
ADMIN_ROLES = ["Director", "HOD", "Dean", "Admin Staff", "HR Manager"]

def get_current_user(request):
    token = request.headers.get("Authorization")
    if not token:
        return None
    payload = verify_token(token)
    return payload

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "No session found"}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Session expired or invalid"}), 401
        request.user = payload
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "No session found"}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Session expired or invalid"}), 401
        if payload["role"] not in ADMIN_ROLES:
            # Log unauthorized attempt
            log_entry = {
                "time": str(datetime.datetime.now()),
                "type": "UNAUTHORIZED_ACCESS",
                "member_id": payload["member_id"],
                "role": payload["role"],
                "endpoint": request.path,
                "method": request.method
            }
            import json, os
            log_path = os.path.join(os.path.dirname(__file__), '../logs/audit.log')
            with open(log_path, 'a') as f2:
                f2.write(json.dumps(log_entry) + '\n')
            return jsonify({"error": "Access denied. Admins only."}), 403
        request.user = payload
        return f(*args, **kwargs)
    return decorated

def is_admin(role):
    return role in ADMIN_ROLES