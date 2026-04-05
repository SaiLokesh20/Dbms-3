"""
CallHub — Locust Stress Test
Module B | CS 432 | IIT Gandhinagar
Run: locust -f scripts/locustfile.py --host=http://127.0.0.1:5000
Then open: http://localhost:8089
"""

import random
from locust import HttpUser, task, between

ADMIN_USERS = [
    {"email": "rohit@org.in",  "password": "9000000009"},
    {"email": "pooja@org.in",  "password": "9000000008"},
]
REGULAR_USERS = [
    {"email": "amit@org.in",   "password": "9000000001"},
]

SEARCH_TERMS = ["sharma", "singh", "kumar", "prof", "iitgn", "test", "admin", "dean"]
INTERACTION_TYPES = ["VIEW_PROFILE", "CLICK_CALL", "CLICK_EMAIL"]


class RegularUser(HttpUser):
    """Simulates a regular student/faculty user — high frequency."""
    weight = 3
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        cred = random.choice(REGULAR_USERS + ADMIN_USERS)
        resp = self.client.post("/login", json=cred, name="/login")
        if resp.status_code == 200:
            self.token = resp.json().get("session_token")

    def on_stop(self):
        if self.token:
            self.client.post("/logout", json={},
                             headers={"Authorization": self.token},
                             name="/logout")

    def auth_headers(self):
        return {"Authorization": self.token}

    @task(4)
    def search_members(self):
        if not self.token:
            return
        term = random.choice(SEARCH_TERMS)
        self.client.post("/search",
                         json={"search_keyword": term},
                         headers=self.auth_headers(),
                         name="/search")

    @task(3)
    def list_members(self):
        if not self.token:
            return
        self.client.get("/members", headers=self.auth_headers(), name="/members")

    @task(2)
    def view_member(self):
        if not self.token:
            return
        mid = random.randint(1, 20)
        self.client.get(f"/members/{mid}", headers=self.auth_headers(),
                        name="/members/[id]")

    @task(2)
    def log_interaction(self):
        if not self.token:
            return
        self.client.post("/interact",
                         json={
                             "target_member_id": random.randint(1, 20),
                             "interaction_type": random.choice(INTERACTION_TYPES)
                         },
                         headers=self.auth_headers(),
                         name="/interact")

    @task(1)
    def list_departments(self):
        if not self.token:
            return
        self.client.get("/departments", headers=self.auth_headers(),
                        name="/departments")

    @task(1)
    def verify_auth(self):
        if not self.token:
            return
        self.client.get("/isAuth", headers=self.auth_headers(), name="/isAuth")


class AdminUser(HttpUser):
    """Simulates an admin user — lower frequency, heavier operations."""
    weight = 1
    wait_time = between(2, 5)
    token = None

    def on_start(self):
        cred = random.choice(ADMIN_USERS)
        resp = self.client.post("/login", json=cred, name="/login")
        if resp.status_code == 200:
            self.token = resp.json().get("session_token")

    def on_stop(self):
        if self.token:
            self.client.post("/logout", json={},
                             headers={"Authorization": self.token},
                             name="/logout")

    def auth_headers(self):
        return {"Authorization": self.token}

    @task(2)
    def view_analytics(self):
        if not self.token:
            return
        self.client.get("/analytics", headers=self.auth_headers(), name="/analytics")

    @task(2)
    def view_login_history(self):
        if not self.token:
            return
        self.client.get("/login-history", headers=self.auth_headers(),
                        name="/login-history")

    @task(2)
    def list_members(self):
        if not self.token:
            return
        self.client.get("/members", headers=self.auth_headers(), name="/members")

    @task(1)
    def add_then_delete_member(self):
        """Add a member and immediately delete — tests write concurrency."""
        if not self.token:
            return
        uid = random.randint(10000, 99999)
        payload = {
            "member_name":   f"Load Test User {uid}",
            "iit_email":     f"loadtest_{uid}@org.in",
            "department_id": 19,
            "primary_phone": f"90{uid}",
            "dob":           "2000-01-01",
            "is_at_campus":  1,
            "role_id":       3,
            "join_date":     "2024-01-01",
        }
        resp = self.client.post("/members", json=payload,
                                headers=self.auth_headers(),
                                name="/members POST")
        if resp.status_code == 201:
            new_id = resp.json().get("member_id")
            if new_id:
                self.client.delete(f"/members/{new_id}",
                                   headers=self.auth_headers(),
                                   name="/members/[id] DELETE")

    @task(1)
    def log_interaction(self):
        if not self.token:
            return
        self.client.post("/interact",
                         json={
                             "target_member_id": random.randint(1, 20),
                             "interaction_type": random.choice(INTERACTION_TYPES)
                         },
                         headers=self.auth_headers(),
                         name="/interact")
