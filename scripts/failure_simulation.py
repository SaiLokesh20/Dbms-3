"""
CallHub — Module B: ACID Failure Simulation Script
CS 432 Databases | Assignment 3 | Team_Randoms | Project 7

Run from Module_B root directory:
    python scripts/failure_simulation.py
"""

import mysql.connector
import threading
import time

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Sailok@1234",   # <-- change this
    "database": "CallHub",
    "autocommit": False,
}

SEPARATOR = "=" * 50

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def print_section(title):
    print(f"\n{SEPARATOR}")
    print(f"TEST: {title}")
    print(SEPARATOR)

def get_valid_ids():
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT department_id FROM Department LIMIT 1")
    dept_id = cursor.fetchone()[0]
    cursor.execute("SELECT role_id FROM Role LIMIT 1")
    role_id = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return dept_id, role_id

def get_unused_member_id():
    conn = get_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(member_id) FROM Member")
    max_id = cursor.fetchone()[0] or 6000
    cursor.close()
    conn.close()
    return max_id + 100


def test_atomicity():
    print_section("1: ATOMICITY")
    print("Scenario: Add member + assign role in one transaction")
    print("Failure : Simulated crash after member insert, before role assignment")
    print(SEPARATOR)

    dept_id, role_id = get_valid_ids()
    test_email = "atomicity_test@iitgn.ac.in"
    test_member_id = get_unused_member_id()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        print("BEGIN TRANSACTION")
        conn.start_transaction()

        print(f"INSERT Member → member_id: {test_member_id}")
        cursor.execute("""
            INSERT INTO Member
                (member_id, member_name, iit_email, primary_phone,
                 dob, department_id, is_at_campus, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (test_member_id, "Atomicity Test", test_email,
              "9000000099", "2000-01-01", dept_id, 1, "2024-01-01"))

        print("SIMULATING FAILURE before role assignment...")
        raise Exception("Simulated system crash!")

        cursor.execute("""
            INSERT INTO Member_Role (member_id, role_id, is_primary)
            VALUES (%s, %s, TRUE)
        """, (test_member_id, role_id))

        conn.commit()

    except Exception as e:
        print(f"FAILURE DETECTED: {e}")
        conn.rollback()
        print("ROLLBACK executed")
    finally:
        cursor.close()
        conn.close()

    conn2 = get_connection()
    conn2.autocommit = True
    cur2 = conn2.cursor()
    cur2.execute("SELECT member_id FROM Member WHERE iit_email = %s", (test_email,))
    result = cur2.fetchone()
    cur2.close()
    conn2.close()

    if result is None:
        print("✅ ATOMICITY VERIFIED: Member does not exist after rollback")
    else:
        print("❌ ATOMICITY FAILED: Partial data found in DB!")


def test_consistency():
    print_section("2: CONSISTENCY")
    print("Scenario: Insert member with invalid department_id (9999)")
    print("Expected: Transaction fails, DB remains consistent")
    print(SEPARATOR)

    test_email = "consistency_test@iitgn.ac.in"
    test_member_id = get_unused_member_id() + 1

    conn = get_connection()
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        print("BEGIN TRANSACTION")
        cursor.execute("""
            INSERT INTO Member
                (member_id, member_name, iit_email, primary_phone,
                 dob, department_id, is_at_campus, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (test_member_id, "Consistency Test", test_email,
              "9000000098", "2000-01-01", 9999, 1, "2024-01-01"))
        conn.commit()
        print("❌ CONSISTENCY FAILED: Invalid member was inserted!")

    except mysql.connector.Error as e:
        print(f"FAILURE DETECTED: {e.errno} ({e.msg[:80]})")
        conn.rollback()
        print("ROLLBACK executed")
        print("✅ CONSISTENCY VERIFIED: Invalid member not inserted")

    finally:
        cursor.close()
        conn.close()


def test_isolation():
    print_section("3: ISOLATION")
    print("Scenario: Two transactions update same member simultaneously")
    print("Expected: Transactions are isolated, no data corruption")
    print(SEPARATOR)

    conn_check = get_connection()
    conn_check.autocommit = True
    cur_check = conn_check.cursor()
    cur_check.execute("SELECT member_id, primary_phone FROM Member LIMIT 1")
    row = cur_check.fetchone()
    cur_check.close()
    conn_check.close()

    if row is None:
        print("❌ No members found in DB — skipping isolation test")
        return

    target_id, original_phone = row
    results = {}

    def transaction_update(thread_name, new_phone):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            print(f"Transaction {thread_name}: BEGIN")
            conn.start_transaction()
            print(f"Transaction {thread_name}: UPDATE member_id={target_id} phone={new_phone}")
            cursor.execute(
                "UPDATE Member SET primary_phone = %s WHERE member_id = %s",
                (new_phone, target_id)
            )
            time.sleep(0.1)
            conn.commit()
            print(f"Transaction {thread_name}: COMMIT")
            cursor.close()
            conn.close()
            results[thread_name] = "committed"
        except Exception as e:
            results[thread_name] = f"error: {e}"

    t1 = threading.Thread(target=transaction_update, args=("T1", "9111111111"))
    t2 = threading.Thread(target=transaction_update, args=("T2", "9222222222"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    conn_final = get_connection()
    conn_final.autocommit = True
    cur_final = conn_final.cursor()
    cur_final.execute("SELECT primary_phone FROM Member WHERE member_id = %s", (target_id,))
    final_phone = cur_final.fetchone()[0]

    cur_final.execute(
        "UPDATE Member SET primary_phone = %s WHERE member_id = %s",
        (original_phone, target_id)
    )
    cur_final.close()
    conn_final.close()

    print(f"Final phone value: {final_phone}")
    if final_phone in ("9111111111", "9222222222"):
        print("✅ ISOLATION VERIFIED: One transaction won, data is consistent")
    else:
        print("❌ ISOLATION FAILED: Unexpected final value!")
    print(f"Original phone restored to {original_phone}")


def test_durability():
    print_section("4: DURABILITY")
    print("Scenario: Insert member, commit, reconnect and verify data persists")
    print(SEPARATOR)

    dept_id, role_id = get_valid_ids()
    test_email = "durability_test@iitgn.ac.in"
    test_member_id = get_unused_member_id() + 2

    conn1 = get_connection()
    cursor1 = conn1.cursor()
    try:
        print("Connection 1: BEGIN TRANSACTION")
        conn1.start_transaction()
        cursor1.execute("""
            INSERT INTO Member
                (member_id, member_name, iit_email, primary_phone,
                 dob, department_id, is_at_campus, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (test_member_id, "Durability Test", test_email,
              "9000000097", "2000-01-01", dept_id, 1, "2024-01-01"))
        conn1.commit()
        print(f"Connection 1: INSERT Member → member_id: {test_member_id}")
        print("Connection 1: COMMIT")
    finally:
        cursor1.close()
        conn1.close()
        print("Connection 1: CLOSED (simulating restart)")

    time.sleep(1)

    conn2 = get_connection()
    conn2.autocommit = True
    cursor2 = conn2.cursor()
    print("Connection 2: New connection opened")
    cursor2.execute("SELECT member_name FROM Member WHERE iit_email = %s", (test_email,))
    result = cursor2.fetchone()

    if result:
        print(f"Connection 2: Found member — {result[0]}")
        print("✅ DURABILITY VERIFIED: Data persists after connection restart")
    else:
        print("❌ DURABILITY FAILED: Member not found after restart!")

    cursor2.execute("DELETE FROM Member WHERE iit_email = %s", (test_email,))
    print("Cleanup: Test member deleted")
    cursor2.close()
    conn2.close()


if __name__ == "__main__":
    print("CallHub — ACID & Failure Simulation Tests")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    test_atomicity()
    test_consistency()
    test_isolation()
    test_durability()

    print(f"\n{SEPARATOR}")
    print("All tests completed!")
    print(SEPARATOR)
