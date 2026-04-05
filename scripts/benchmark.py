import mysql.connector
import time
import statistics
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Sailok@1234",  #password
    "database": "CallHub"
}

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../benchmark_results.txt")


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def timed(cursor, query, params=(), runs=10):
    samples = []
    for _ in range(runs):
        start = time.perf_counter()
        cursor.execute(query, params)
        cursor.fetchall()
        samples.append(time.perf_counter() - start)
    return statistics.mean(samples)


def explain(cursor, query, params=()):
    cursor.execute("EXPLAIN " + query, params)
    return cursor.fetchall()


def drop_indexes(cursor):
    indexes = [
        ("Member", "idx_member_name"),
        ("Member", "idx_member_email"),
        ("Member", "idx_member_dept"),
        ("Member_Role", "idx_member_role_mid"),
        ("Search_Log", "idx_search_time"),
        ("Directory_Interaction_Log", "idx_interaction_actor"),
        ("Directory_Interaction_Log", "idx_interaction_target"),
        ("Login_History", "idx_login_member"),
        ("Audit_Log", "idx_audit_performed"),
    ]
    for table, idx in indexes:
        try:
            cursor.execute(f"DROP INDEX {idx} ON {table}")
            print(f"Dropped: {idx}")
        except Exception as e:
            print(f"Skip drop {idx}: {e}")


def apply_indexes(cursor):
    indexes = [
        "CREATE INDEX idx_member_name ON Member(member_name)",
        "CREATE INDEX idx_member_email ON Member(iit_email)",
        "CREATE INDEX idx_member_dept ON Member(department_id)",
        "CREATE INDEX idx_member_role_mid ON Member_Role(member_id)",
        "CREATE INDEX idx_search_time ON Search_Log(search_time)",
        "CREATE INDEX idx_interaction_actor ON Directory_Interaction_Log(actor_member_id)",
        "CREATE INDEX idx_interaction_target ON Directory_Interaction_Log(target_member_id)",
        "CREATE INDEX idx_login_member ON Login_History(member_id)",
        "CREATE INDEX idx_audit_performed ON Audit_Log(performed_by_member_id)",
    ]
    for idx in indexes:
        try:
            cursor.execute(idx)
            print(f"Created: {idx.split('ON')[1]}")
        except Exception as e:
            print(f"Skip create: {e}")


# Queries to benchmark
Q1 = """
    SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
           d.department_name, r.role_name
    FROM Member m
    JOIN Department d ON m.department_id = d.department_id
    JOIN Member_Role mr ON m.member_id = mr.member_id
    JOIN Role r ON mr.role_id = r.role_id
    WHERE mr.is_primary = TRUE
    AND m.exit_date IS NULL
    AND m.member_name LIKE '%test%'
"""

Q2 = """
    SELECT m.member_id, m.member_name, m.iit_email
    FROM Member m
    JOIN Member_Role mr ON m.member_id = mr.member_id
    WHERE m.department_id = %s
    AND mr.is_primary = TRUE
    AND m.exit_date IS NULL
"""

Q3 = """
    SELECT m.member_id, m.member_name
    FROM Member m
    WHERE m.iit_email LIKE '%org.in%'
    AND m.exit_date IS NULL
"""


def run_benchmark(apply=False):
    conn = get_conn()
    cursor = conn.cursor()

    if apply:
        print("\nApplying indexes...")
        apply_indexes(cursor)
        conn.commit()
    else:
        print("\nDropping indexes for clean baseline...")
        drop_indexes(cursor)
        conn.commit()

    label = "WITH indexes" if apply else "WITHOUT indexes"
    print(f"\nBenchmarking {label}...")

    q1_avg = timed(cursor, Q1)
    q2_avg = timed(cursor, Q2, (1,))
    q3_avg = timed(cursor, Q3)

    q1_explain = explain(cursor, Q1)
    q2_explain = explain(cursor, Q2, (1,))
    q3_explain = explain(cursor, Q3)

    cursor.close()
    conn.close()

    return {
        "label": label,
        "q1_avg_s": q1_avg,
        "q2_avg_s": q2_avg,
        "q3_avg_s": q3_avg,
        "q1_explain": q1_explain,
        "q2_explain": q2_explain,
        "q3_explain": q3_explain,
    }


def main():
    print("=" * 50)
    print("CallHub - SQL Index Benchmark")
    print("=" * 50)

    # Get total member count
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Member")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"Total members in DB: {total}")

    before = run_benchmark(apply=False)
    after = run_benchmark(apply=True)

    # Calculate improvements
    q1_imp = ((before["q1_avg_s"] - after["q1_avg_s"]) / before["q1_avg_s"]) * 100
    q2_imp = ((before["q2_avg_s"] - after["q2_avg_s"]) / before["q2_avg_s"]) * 100
    q3_imp = ((before["q3_avg_s"] - after["q3_avg_s"]) / before["q3_avg_s"]) * 100

    lines = []
    lines.append("CallHub Module B - Index Benchmark Results")
    lines.append("=" * 50)
    lines.append(f"Total members benchmarked: {total}")
    lines.append("")
    lines.append("SQL Query Timings (seconds):")
    lines.append("-" * 40)
    lines.append("Q1: Search by name with JOINs (LIKE '%test%')")
    lines.append(f"  Before index avg: {before['q1_avg_s']:.6f}s")
    lines.append(f"  After  index avg: {after['q1_avg_s']:.6f}s")
    lines.append(f"  Improvement     : {q1_imp:.1f}%")
    lines.append("")
    lines.append("Q2: Filter by department with JOIN")
    lines.append(f"  Before index avg: {before['q2_avg_s']:.6f}s")
    lines.append(f"  After  index avg: {after['q2_avg_s']:.6f}s")
    lines.append(f"  Improvement     : {q2_imp:.1f}%")
    lines.append("")
    lines.append("Q3: Search by email")
    lines.append(f"  Before index avg: {before['q3_avg_s']:.6f}s")
    lines.append(f"  After  index avg: {after['q3_avg_s']:.6f}s")
    lines.append(f"  Improvement     : {q3_imp:.1f}%")
    lines.append("")
    lines.append("EXPLAIN Plans:")
    lines.append("-" * 40)
    lines.append("Q1 BEFORE indexes:")
    for row in before["q1_explain"]:
        lines.append(f"  {row}")
    lines.append("")
    lines.append("Q1 AFTER indexes:")
    for row in after["q1_explain"]:
        lines.append(f"  {row}")
    lines.append("")
    lines.append("Q2 BEFORE indexes:")
    for row in before["q2_explain"]:
        lines.append(f"  {row}")
    lines.append("")
    lines.append("Q2 AFTER indexes:")
    for row in after["q2_explain"]:
        lines.append(f"  {row}")
    lines.append("")
    lines.append("Q3 BEFORE indexes:")
    for row in before["q3_explain"]:
        lines.append(f"  {row}")
    lines.append("")
    lines.append("Q3 AFTER indexes:")
    for row in after["q3_explain"]:
        lines.append(f"  {row}")

    output = "\n".join(lines)
    print("\n" + output)

    with open(OUTPUT_PATH, "w") as f:
        f.write(output)

    print(f"\nSaved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()