USE CallHub;

-- ---------------- DEPARTMENT ----------------
INSERT INTO Department (department_name, building, opening_hours, closing_hours) VALUES
('Computer Science','Block A','09:00:00','17:00:00'),
('Information Technology','Block A','09:00:00','17:00:00'),
('Electrical Engineering','Block B','09:00:00','17:00:00'),
('Mechanical Engineering','Block C','09:00:00','17:00:00'),
('Civil Engineering','Block D','09:00:00','17:00:00'),
('Electronics','Block E','09:00:00','17:00:00'),
('Data Science','Block F','09:00:00','17:00:00'),
('AI','Block F','09:00:00','17:00:00'),
('Cyber Security','Block G','09:00:00','17:00:00'),
('Administration','Admin','09:00:00','17:00:00'),
('Accounts','Admin','09:00:00','17:00:00'),
('HR','Admin','09:00:00','17:00:00'),
('Library','Library','08:00:00','20:00:00'),
('Hostel','Hostel','09:00:00','18:00:00'),
('Placement','Placement','09:00:00','17:00:00'),
('Research','R&D','09:00:00','17:00:00'),
('IT Support','IT','09:00:00','18:00:00'),
('Security','Gate','00:00:00','23:59:00'),
('Medical','Medical','09:00:00','18:00:00'),
('Exam Cell','Admin','09:00:00','17:00:00');

-- ---------------- ROLE ----------------
INSERT INTO Role (role_name) VALUES
('Student'),('Professor'),('Assistant Professor'),('Associate Professor'),
('Lab Assistant'),('Technician'),('HOD'),('Dean'),('Director'),
('Admin Staff'),('Account Officer'),('HR Manager'),
('Librarian'),('Hostel Warden'),('Security Guard'),
('Doctor'),('Nurse'),('IT Engineer'),
('Placement Officer'),('Research Scholar');

-- ---------------- PERMISSION ----------------
INSERT INTO Permission (permission_name) VALUES
('VIEW_CONTACT'),('EDIT_CONTACT'),('DELETE_CONTACT'),
('EXPORT'),('EMERGENCY'),('VIEW_ANALYTICS'),
('ADD_MEMBER'),('REMOVE_MEMBER'),('ASSIGN_ROLE'),
('LOGIN'),('LOGOUT'),('VIEW_DEPT'),
('ADD_DEPT'),('DELETE_DEPT'),('UPDATE_DEPT'),
('SEARCH'),('CALL'),('EMAIL'),
('VIEW_PROFILE'),('ADMIN_ACCESS');

-- ---------------- ROLE_PERMISSION ----------------
INSERT INTO Role_Permission (role_id, permission_id) VALUES
(1,1),(1,10),
(2,1),(2,6),
(3,1),(3,6),
(4,1),(4,6),
(5,1),(5,7),
(6,1),(6,7),
(7,1),(7,2),
(8,1),(8,2),
(9,1),(9,4),
(10,1),(10,2);

-- ---------------- MEMBER ----------------
INSERT INTO Member
(member_name,iit_email,primary_phone,dob,department_id,is_at_campus,join_date)
VALUES
('Amit Sharma','amit@org.in','9000000001','2000-01-01',1,TRUE,'2022-07-01'),
('Priya Verma','priya@org.in','9000000002','1999-02-02',2,TRUE,'2021-07-01'),
('Rahul Mehta','rahul@org.in','9000000003','2001-03-03',3,TRUE,'2023-01-01'),
('Sneha Iyer','sneha@org.in','9000000004','1998-04-04',4,TRUE,'2020-07-01'),
('Karan Patel','karan@org.in','9000000005','1997-05-05',5,TRUE,'2019-07-01'),
('Neha Gupta','neha@org.in','9000000006','2000-06-06',6,TRUE,'2022-01-01'),
('Arjun Nair','arjun@org.in','9000000007','1996-07-07',7,TRUE,'2018-01-01'),
('Pooja Singh','pooja@org.in','9000000008','1995-08-08',8,TRUE,'2017-01-01'),
('Rohit Das','rohit@org.in','9000000009','1994-09-09',9,TRUE,'2016-01-01'),
('Ananya Rao','ananya@org.in','9000000010','2002-10-10',10,TRUE,'2023-07-01'),
('Vikas Kumar','vikas@org.in','9000000011','1993-01-11',11,TRUE,'2015-01-01'),
('Meera Pillai','meera@org.in','9000000012','1992-02-12',12,TRUE,'2014-01-01'),
('Suresh Reddy','suresh@org.in','9000000013','1991-03-13',13,TRUE,'2013-01-01'),
('Kavita Joshi','kavita@org.in','9000000014','1990-04-14',14,TRUE,'2012-01-01'),
('Manoj Yadav','manoj@org.in','9000000015','1989-05-15',15,TRUE,'2011-01-01'),
('Deepak Jain','deepak@org.in','9000000016','1988-06-16',16,TRUE,'2010-01-01'),
('Farhan Ali','farhan@org.in','9000000017','1987-07-17',17,TRUE,'2009-01-01'),
('Ritu Saxena','ritu@org.in','9000000018','1999-08-18',18,TRUE,'2021-01-01'),
('Nikhil Bansal','nikhil@org.in','9000000019','1998-09-19',19,TRUE,'2020-01-01'),
('Tanya Kapoor','tanya@org.in','9000000020','2001-10-20',20,TRUE,'2023-08-01');

-- ---------------- MEMBER_ROLE ----------------
INSERT INTO Member_Role (member_id,role_id,is_primary,start_date) VALUES
(1,1,TRUE,'2022-07-01'),
(2,2,TRUE,'2021-07-01'),
(3,1,TRUE,'2023-01-01'),
(4,3,TRUE,'2020-07-01'),
(5,4,TRUE,'2019-07-01'),
(6,1,TRUE,'2022-01-01'),
(7,5,TRUE,'2018-01-01'),
(8,7,TRUE,'2017-01-01'),
(9,9,TRUE,'2016-01-01'),
(10,10,TRUE,'2023-07-01'),
(11,11,TRUE,'2015-01-01'),
(12,12,TRUE,'2014-01-01'),
(13,13,TRUE,'2013-01-01'),
(14,14,TRUE,'2012-01-01'),
(15,15,TRUE,'2011-01-01'),
(16,19,TRUE,'2010-01-01'),
(17,20,TRUE,'2009-01-01'),
(18,18,TRUE,'2021-01-01'),
(19,19,TRUE,'2020-01-01'),
(20,1,TRUE,'2023-08-01');

-- ---------------- MEMBER_CONTACT ----------------
INSERT INTO Member_Contact (member_id,contact_type,contact_value,is_primary) VALUES
(1,'ALT_PHONE','8000000001',FALSE),(2,'ALT_PHONE','8000000002',FALSE),
(3,'ALT_PHONE','8000000003',FALSE),(4,'ALT_PHONE','8000000004',FALSE),
(5,'ALT_PHONE','8000000005',FALSE),(6,'ALT_PHONE','8000000006',FALSE),
(7,'ALT_PHONE','8000000007',FALSE),(8,'ALT_PHONE','8000000008',FALSE),
(9,'ALT_PHONE','8000000009',FALSE),(10,'ALT_PHONE','8000000010',FALSE),
(11,'ALT_PHONE','8000000011',FALSE),(12,'ALT_PHONE','8000000012',FALSE),
(13,'ALT_PHONE','8000000013',FALSE),(14,'ALT_PHONE','8000000014',FALSE),
(15,'ALT_PHONE','8000000015',FALSE),(16,'ALT_PHONE','8000000016',FALSE),
(17,'ALT_PHONE','8000000017',FALSE),(18,'ALT_PHONE','8000000018',FALSE),
(19,'ALT_PHONE','8000000019',FALSE),(20,'ALT_PHONE','8000000020',FALSE);

-- ---------------- LAB ----------------
INSERT INTO Lab (lab_name, department_id, building, room_no, contact_no, incharge_member_id) VALUES
('AI Lab',8,'Block F','F201','7100000001',8),
('Robotics Lab',4,'Block C','C301','7100000002',5),
('Power Systems Lab',3,'Block B','B210','7100000003',3),
('Civil Survey Lab',5,'Block D','D102','7100000004',4),
('Electronics Lab',6,'Block E','E110','7100000005',6);

-- ---------------- OFFICE_ROOM ----------------
INSERT INTO Office_Room (department_id, building, room_no, office_contact) VALUES
(1,'Block A','101','7200000001'),
(2,'Block A','102','7200000002'),
(3,'Block B','103','7200000003'),
(4,'Block C','104','7200000004'),
(5,'Block D','105','7200000005');

-- ---------------- SEARCH_LOG ----------------
INSERT INTO Search_Log
(member_id, search_keyword, search_time, result_count, filter_department_id, filter_role_id)
VALUES
(1,'Rahul','2026-01-01 10:00:00',3,1,1),
(2,'Library','2026-01-02 11:00:00',5,13,13),
(3,'Hostel','2026-01-03 12:00:00',2,14,14);

-- ---------------- DIRECTORY_INTERACTION_LOG ----------------
INSERT INTO Directory_Interaction_Log
(actor_member_id,target_member_id,interaction_type,interaction_time)
VALUES
(1,2,'CLICK_CALL','2026-02-01 10:00:00'),
(2,3,'VIEW_PROFILE','2026-02-01 11:00:00');

-- ---------------- LOGIN_HISTORY ----------------
INSERT INTO Login_History
(member_id,login_time,logout_time,ip_address)
VALUES
(1,'2026-02-01 09:00:00','2026-02-01 10:00:00','192.168.1.1'),
(2,'2026-02-01 09:05:00','2026-02-01 10:05:00','192.168.1.2');

-- ---------------- AUDIT_LOG ----------------
INSERT INTO Audit_Log
(performed_by_member_id,target_member_id,action_type,affected_table,affected_row_pk,action_time)
VALUES
(9,1,'INSERT','Member','1','2026-02-01 12:00:00'),
(9,2,'UPDATE','Member','2','2026-02-01 12:05:00');
