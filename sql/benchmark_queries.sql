-- CallHub Module B - Benchmark Queries
-- These are the queries benchmarked before and after indexing
-- Tested with 5020 members in the CallHub MySQL database

USE CallHub;

-- ─────────────────────────────────────────────────────────
-- QUERY 1: Search members by name with multiple JOINs
-- Used in: /search API endpoint
-- Indexes targeted: idx_member_name, idx_member_role_mid
-- ─────────────────────────────────────────────────────────
SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
       d.department_name, r.role_name
FROM Member m
JOIN Department d ON m.department_id = d.department_id
JOIN Member_Role mr ON m.member_id = mr.member_id
JOIN Role r ON mr.role_id = r.role_id
WHERE mr.is_primary = TRUE
AND m.exit_date IS NULL
AND m.member_name LIKE '%test%';

-- EXPLAIN plan for Query 1
EXPLAIN SELECT m.member_id, m.member_name, m.iit_email, m.primary_phone,
               d.department_name, r.role_name
FROM Member m
JOIN Department d ON m.department_id = d.department_id
JOIN Member_Role mr ON m.member_id = mr.member_id
JOIN Role r ON mr.role_id = r.role_id
WHERE mr.is_primary = TRUE
AND m.exit_date IS NULL
AND m.member_name LIKE '%test%';


-- ─────────────────────────────────────────────────────────
-- QUERY 2: Filter members by department with JOIN
-- Used in: /members API with department filter
-- Indexes targeted: idx_member_dept, idx_member_role_mid
-- ─────────────────────────────────────────────────────────
SELECT m.member_id, m.member_name, m.iit_email
FROM Member m
JOIN Member_Role mr ON m.member_id = mr.member_id
WHERE m.department_id = 1
AND mr.is_primary = TRUE
AND m.exit_date IS NULL;

-- EXPLAIN plan for Query 2
EXPLAIN SELECT m.member_id, m.member_name, m.iit_email
FROM Member m
JOIN Member_Role mr ON m.member_id = mr.member_id
WHERE m.department_id = 1
AND mr.is_primary = TRUE
AND m.exit_date IS NULL;


-- ─────────────────────────────────────────────────────────
-- QUERY 3: Search members by email
-- Used in: /login API and /search API
-- Indexes targeted: idx_member_email
-- ─────────────────────────────────────────────────────────
SELECT m.member_id, m.member_name
FROM Member m
WHERE m.iit_email LIKE '%org.in%'
AND m.exit_date IS NULL;

-- EXPLAIN plan for Query 3
EXPLAIN SELECT m.member_id, m.member_name
FROM Member m
WHERE m.iit_email LIKE '%org.in%'
AND m.exit_date IS NULL;


-- ─────────────────────────────────────────────────────────
-- INDEXES APPLIED
-- ─────────────────────────────────────────────────────────
-- CREATE INDEX idx_member_name ON Member(member_name);
-- CREATE INDEX idx_member_email ON Member(iit_email);
-- CREATE INDEX idx_member_dept ON Member(department_id);
-- CREATE INDEX idx_member_role_mid ON Member_Role(member_id);
-- CREATE INDEX idx_search_time ON Search_Log(search_time);
-- CREATE INDEX idx_interaction_actor ON Directory_Interaction_Log(actor_member_id);
-- CREATE INDEX idx_interaction_target ON Directory_Interaction_Log(target_member_id);
-- CREATE INDEX idx_login_member ON Login_History(member_id);
-- CREATE INDEX idx_audit_performed ON Audit_Log(performed_by_member_id);


-- ─────────────────────────────────────────────────────────
-- BENCHMARK RESULTS SUMMARY
-- ─────────────────────────────────────────────────────────
-- Total members: 5020
-- Q1 before: 2.6477ms  | after: 1.5132ms  | improvement: 42.85%
-- Q2 before: 0.000664s | after: 0.000556s  | improvement: 16.3%
-- MySQL profiling: before: 0.01918100s | after: 0.00773400s | improvement: 59.7%
-- Full results in: benchmark_results.txt
