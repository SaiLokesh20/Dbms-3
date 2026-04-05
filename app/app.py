from flask import Flask, render_template, redirect
from auth import auth_bp
from routes.members import members_bp
from routes.departments import departments_bp
from routes.analytics import analytics_bp
from flask import Flask, render_template, redirect, request, jsonify
from routes.requests import requests_bp

app = Flask(__name__)
app.secret_key = "callhub_secret_key"

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(members_bp)
app.register_blueprint(departments_bp)
app.register_blueprint(analytics_bp)

# PAGE ROUTES 


def home():
    return redirect("/login")

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/page/members")
def members_page():
    return render_template("members.html")

@app.route("/page/departments")
def departments_page():
    return render_template("departments.html")

@app.route("/page/analytics")
def analytics_page():
    return render_template("analytics.html")

@app.route("/portfolio/<int:member_id>")
def portfolio_page(member_id):
    return render_template("portfolio.html", member_id=member_id)

app.register_blueprint(requests_bp)

@app.route("/page/requests")
def requests_page():
    return render_template("requests.html")

@app.route("/roles")
def get_roles():
    from auth import verify_token
    token = request.headers.get("Authorization")
    if not token or not verify_token(token):
        return {"error": "Unauthorized"}, 401
    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT role_id, role_name FROM Role")
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return roles

if __name__ == "__main__":
    app.run(debug=True)