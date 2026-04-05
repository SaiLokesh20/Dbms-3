CREATE DATABASE IF NOT EXISTS CallHub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE CallHub;

-- =========================
-- DROP TABLES (safe reset)
-- =========================
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Audit_Log;
DROP TABLE IF EXISTS Login_History;
DROP TABLE IF EXISTS Search_Log;
DROP TABLE IF EXISTS Role_Permission;
DROP TABLE IF EXISTS Permission;
DROP TABLE IF EXISTS Directory_Interaction_Log;
DROP TABLE IF EXISTS Office_Room;
DROP TABLE IF EXISTS Lab;
DROP TABLE IF EXISTS Hostel;
DROP TABLE IF EXISTS Member_Contact;
DROP TABLE IF EXISTS Member_Role;
DROP TABLE IF EXISTS Role;
DROP TABLE IF EXISTS Member;
DROP TABLE IF EXISTS Department;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- SCHEMA
-- =========================

CREATE TABLE Department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    building VARCHAR(100) NOT NULL,
    opening_hours TIME NOT NULL,
    closing_hours TIME NOT NULL,
    hod_member_id INT NULL
);

CREATE TABLE Member (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    member_name VARCHAR(100) NOT NULL,
    iit_email VARCHAR(150) UNIQUE NOT NULL,
    primary_phone VARCHAR(15) NOT NULL,
    dob DATE NOT NULL,
    image BLOB NULL,
    department_id INT NOT NULL,
    is_at_campus BOOLEAN NOT NULL,
    join_date DATE NOT NULL,
    exit_date DATE NULL,
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

CREATE TABLE Role (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE Member_Role (
    member_id INT NOT NULL,
    role_id INT NOT NULL,
    is_primary BOOLEAN NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    PRIMARY KEY (member_id, role_id, start_date),
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (role_id) REFERENCES Role(role_id)
);

CREATE TABLE Member_Contact (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    contact_type ENUM('PERSONAL_EMAIL','EMERGENCY_PHONE','ADDRESS','ALT_PHONE') NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Member(member_id)
);

CREATE TABLE Hostel (
    hostel_id INT AUTO_INCREMENT PRIMARY KEY,
    hostel_name VARCHAR(100) UNIQUE NOT NULL,
    caretaker_member_id INT NULL,
    caretaker_contact VARCHAR(20),
    FOREIGN KEY (caretaker_member_id) REFERENCES Member(member_id)
);

CREATE TABLE Lab (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    lab_name VARCHAR(100) NOT NULL,
    department_id INT NOT NULL,
    building VARCHAR(100) NOT NULL,
    room_no VARCHAR(20) NOT NULL,
    contact_no VARCHAR(20),
    incharge_member_id INT NULL,
    FOREIGN KEY (department_id) REFERENCES Department(department_id),
    FOREIGN KEY (incharge_member_id) REFERENCES Member(member_id)
);

CREATE TABLE Office_Room (
    office_room_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    building VARCHAR(100) NOT NULL,
    room_no VARCHAR(20) NOT NULL,
    office_contact VARCHAR(20),
    FOREIGN KEY (department_id) REFERENCES Department(department_id)
);

CREATE TABLE Directory_Interaction_Log (
    interaction_id INT AUTO_INCREMENT PRIMARY KEY,
    actor_member_id INT NOT NULL,
    target_member_id INT NOT NULL,
    interaction_type ENUM('VIEW_PROFILE','CLICK_CALL','CLICK_EMAIL') NOT NULL,
    interaction_time DATETIME NOT NULL,
    FOREIGN KEY (actor_member_id) REFERENCES Member(member_id),
    FOREIGN KEY (target_member_id) REFERENCES Member(member_id)
);

CREATE TABLE Permission (
    permission_id INT AUTO_INCREMENT PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE Role_Permission (
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES Role(role_id),
    FOREIGN KEY (permission_id) REFERENCES Permission(permission_id)
);

CREATE TABLE Search_Log (
    search_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    search_keyword VARCHAR(100) NOT NULL,
    search_time DATETIME NOT NULL,
    result_count INT NOT NULL,
    filter_department_id INT NULL,
    filter_role_id INT NULL,
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (filter_department_id) REFERENCES Department(department_id),
    FOREIGN KEY (filter_role_id) REFERENCES Role(role_id)
);

CREATE TABLE Login_History (
    login_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    login_time DATETIME NOT NULL,
    logout_time DATETIME NULL,
    ip_address VARCHAR(50) NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Member(member_id)
);

CREATE TABLE Audit_Log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    performed_by_member_id INT NOT NULL,
    target_member_id INT NULL,
    action_type ENUM('INSERT','UPDATE','DELETE','EXPORT','EMERGENCY_VIEW') NOT NULL,
    affected_table VARCHAR(100) NOT NULL,
    affected_row_pk VARCHAR(100) NOT NULL,
    old_data JSON NULL,
    new_data JSON NULL,
    action_time DATETIME NOT NULL,
    retention_until DATE NULL,
    FOREIGN KEY (performed_by_member_id) REFERENCES Member(member_id),
    FOREIGN KEY (target_member_id) REFERENCES Member(member_id)
);

DROP TABLE IF EXISTS Edit_Request;

CREATE TABLE Edit_Request (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    requested_name VARCHAR(100) NULL,
    requested_phone VARCHAR(15) NULL,
    requested_campus BOOLEAN NULL,
    status ENUM('PENDING', 'ACCEPTED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    requested_at DATETIME NOT NULL,
    reviewed_at DATETIME NULL,
    reviewed_by INT NULL,
    FOREIGN KEY (member_id) REFERENCES Member(member_id),
    FOREIGN KEY (reviewed_by) REFERENCES Member(member_id)
);


ALTER TABLE Department
ADD CONSTRAINT fk_hod
FOREIGN KEY (hod_member_id) REFERENCES Member(member_id);

